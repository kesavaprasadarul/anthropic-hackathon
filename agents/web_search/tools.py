import json
from smolagents import Tool
from typing import List, Dict, Any, Tuple, Optional
from .globals import GOOGLE_MAPS_KEY
import requests
import datetime as dt
from zoneinfo import ZoneInfo
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import unicodedata



PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACES_SEARCH_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"

PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/"

PLACES_FIELDS = (
    "places.id,places.displayName,places.rating,places.userRatingCount,places.priceLevel,"
    "places.formattedAddress,places.servesVegetarianFood,places.nationalPhoneNumber,"
    "places.websiteUri,places.businessStatus,places.currentOpeningHours,places.types"
)

def _parse_iso(s: str) -> dt.datetime:
    """Parse ISO 8601, accepting 'Z'."""
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

def _to_utc_iso(d: dt.datetime) -> str:
    """Return RFC3339 UTC with 'Z'."""
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    else:
        d = d.astimezone(dt.timezone.utc)
    return d.isoformat().replace("+00:00", "Z")

class CombinedReservationSearchTool(Tool):
    name = "search_and_reservations"
    description = (
        "Search Google Places using a text query, then for the first N (default 5) places, "
        "attempt to detect reservation options from their website and extract available times. "
        "Returns an array of JSON objects per place."
    )
    inputs = {
        "text_query": {"type": "string", "description": "Free-form search text (e.g., 'best sushi Berlin')"},
        "latitude": {"type": "number", "description": "Latitude for location bias", "optional": True, "nullable": True},
        "longitude": {"type": "number", "description": "Longitude for location bias", "optional": True, "nullable": True},
        "radius": {"type": "integer", "description": "Radius in meters for location bias (default 1000)", "optional": True, "nullable": True},
        "max_places": {"type": "integer", "description": "How many places to fetch (default 5, max 10)", "optional": True, "nullable": True},
    }
    output_type = "array"

    # ---- HTTP / scraping config ----
    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }
    _TIMEOUT = 10  # seconds
    _MAX_WORKERS = 5

    # reservation keyword hints
    _RESERVE_KEYWORDS = [
        # EN
        "reserve", "reservation", "book", "book a table", "booking", "table",
        # DE
        "reservieren", "reservierung", "tisch reservieren", "tisch buchen", "buchen",
        # FR/ES/IT/NL + common variants
        "réserver", "reserver", "reserva", "prenota", "boeking", "online buchen",
        # common providers spelled out too
        "open table", "opentable", "thefork", "quandoo", "resmio", "tock", "formitable",
        "bookatable", "sevenrooms", "yelp", "chope", "resy", "eatapp",
    ]
    _RESERVE_DOMAINS = [
        "opentable", "thefork", "lafourchette", "quandoo", "resmio", "tock", "exploretock",
        "formitable", "bookatable", "sevenrooms", "yelp", "chope", "tablein", "guestonline",
        "resy", "eatapp", "zoma.to", "zomato"
    ]
    _TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):[0-5]\d\b")

    # -------- Helpers --------
    def _normalize_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        url = url.strip()
        if not url:
            return None
        parsed = urlparse(url)
        if not parsed.scheme:
            return "https://" + url.lstrip("/")
        return url

    def _fetch(self, url: str) -> Optional[str]:
        try:
            resp = requests.get(url, headers=self._HEADERS, timeout=self._TIMEOUT)
            ctype = resp.headers.get("Content-Type", "")
            if 200 <= resp.status_code < 300 and "text" in ctype:
                return resp.text
        except Exception:
            pass
        return None

    def _looks_like_reservation_link(self, href: str, text: str) -> bool:
        h = href.lower()
        t = (text or "").lower()
        if any(k in t for k in self._RESERVE_KEYWORDS):
            return True
        if any(k in h for k in self._RESERVE_KEYWORDS):
            return True
        if any(dom in h for dom in self._RESERVE_DOMAINS):
            return True
        return False

    def _find_reservation_link(self, base_url: str, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "html.parser")

        # Priority: explicit buttons/links
        for tag in soup.find_all(["a", "button"]):
            href = tag.get("href") or ""
            text = tag.get_text(" ", strip=True) or ""
            if href and self._looks_like_reservation_link(href, text):
                return urljoin(base_url, href)

        # Embedded provider iframes
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "") or ""
            if src and any(dom in src.lower() for dom in self._RESERVE_DOMAINS):
                return urljoin(base_url, src)

        # Fallback: common slugs
        common_slugs = ["reserv", "reservation", "reservierung", "booking", "book", "tisch", "table"]
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(slug in href.lower() for slug in common_slugs):
                return urljoin(base_url, href)

        return None

    def _extract_times(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(" ", strip=True)
        times = {m.group(0) for m in self._TIME_RE.finditer(text)}
        def key(t: str) -> int:
            h, m = t.split(":")
            return int(h) * 60 + int(m)
        return sorted(times, key=key)

    def _places_search(self, text_query: str, latitude: Optional[float], longitude: Optional[float], radius: Optional[int]) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "textQuery": text_query,
            "maxResultCount": 1,
            "rankPreference": "RELEVANCE",
        }
        if latitude is not None and longitude is not None:
            payload["locationBias"] = {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": radius or 1000,
                }
            }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_KEY,
            "X-Goog-FieldMask": PLACES_FIELDS,
        }
        resp = requests.post(
            PLACES_SEARCH_TEXT_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("places", [])

    def _reservation_for_place(self, place: Dict[str, Any]) -> Dict[str, Any]:
        name = (place.get("displayName") or {}).get("text") or place.get("name") or ""
        website = place.get("websiteUri") or ""
        phone = place.get("nationalPhoneNumber") or ""
        address = place.get("formattedAddress") or ""
        pid = place.get("id") or ""

        hours = place.get("currentOpeningHours") or {}
        weekday_desc = hours.get("weekdayDescriptions") or []

        # Join list -> single string, normalize safely
        if isinstance(weekday_desc, list):
            raw_hours_text = " | ".join(str(x) for x in weekday_desc)
        else:
            raw_hours_text = str(weekday_desc)

        # Normalize
        norm_hours_text = unicodedata.normalize("NFKC", raw_hours_text) \
            .replace("\u202f", " ") \
            .replace("\u2009", " ")

        # Split on the separators Google returns (" | ")
        parts = [p.strip() for p in norm_hours_text.split("|") if p.strip()]

        # Option A: dict keyed by weekday
        available_times = {}
        for p in parts:
            if ":" in p:
                day, hours = p.split(":", 1)
                available_times[day.strip()] = hours.strip()

        # Option B (better): extract HH:MM times from the text using your _TIME_RE
        # available_times = sorted({m.group(0) for m in self._TIME_RE.finditer(norm_hours_text)},
        #                         key=lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]))

        return {
            "name": name,
            "id": pid,
            "address": address,
            "phone": phone,
            "website": website,
            "rating": place.get("rating"),
            "reviews": place.get("userRatingCount"),
            "price": place.get("priceLevel"),
            "status": place.get("businessStatus"),
            "types": place.get("types", []),
            "reservation_url": (website.rstrip("/") + "/reservierung") if website else "",
            "available_times": available_times,  # now a list like ["10:00","12:30",...]
        }


    # -------- Tool entrypoint --------
    def forward(
        self,
        text_query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[int] = None,
        max_places: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        try:
            places = self._places_search(text_query, latitude, longitude, radius)
        except requests.exceptions.HTTPError as e:
            return [{"error": f"HTTP Error: {e.response.status_code} - {e.response.text}"}]
        except requests.exceptions.RequestException as e:
            return [{"error": f"Request failed: {e}"}]

        if not places:
            return [{"message": "No places matched the text query."}]

        n = max(1, min(max_places or 5, 10))
        top = places[:n]

        results: List[Dict[str, Any]] = []

        # Fetch reservation info in parallel for speed
        with ThreadPoolExecutor(max_workers=self._MAX_WORKERS) as ex:
            future_map = {ex.submit(self._reservation_for_place, p): p for p in top}
            for fut in as_completed(future_map):
                print(fut)
                try:
                    results.append(fut.result())
                except Exception as e:
                    place = future_map[fut]
                    name = (place.get("displayName") or {}).get("text") or place.get("name") or ""
                    results.append({"name": name, "error": f"Reservation scrape failed: {e}"})

        # Keep original search order (optional)
        order: Dict[str, int] = {}
        for idx, p in enumerate(top):
            pid = p.get("id") or p.get("placeId") or ((p.get("displayName") or {}).get("text") or str(idx))
            order[pid] = idx
        results.sort(key=lambda r: order.get(r.get("place_id") or r.get("name"), 1_000_000))

        return results


GOOGLE_FREEBUSY_URL = "https://www.googleapis.com/calendar/v3/freeBusy"
GOOGLE_EVENTS_URL_TMPL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

def _bearer_headers(access_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

def _merge_intervals(intervals: List[Tuple[dt.datetime, dt.datetime]]) -> List[Tuple[dt.datetime, dt.datetime]]:
    """Merge overlapping [start, end) intervals."""
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged

def _invert_busy_to_free(
    busy: List[Tuple[dt.datetime, dt.datetime]],
    day_start: dt.datetime,
    day_end: dt.datetime
) -> List[Tuple[dt.datetime, dt.datetime]]:
    """Given busy intervals within a day's working window, return free gaps."""
    free = []
    cursor = day_start
    for b_start, b_end in busy:
        if b_end <= day_start or b_start >= day_end:
            continue
        b_start = max(b_start, day_start)
        b_end = min(b_end, day_end)
        if cursor < b_start:
            free.append((cursor, b_start))
        cursor = max(cursor, b_end)
    if cursor < day_end:
        free.append((cursor, day_end))
    return free

class GoogleCalendarAvailabilityTool(Tool):
    name = "google_calendar_availability"
    description = (
        "Get availability (free/busy) for the next N days by checking Google Calendar via FreeBusy. "
        "Returns busy blocks and computed free windows per day within working hours."
    )
    inputs = {
        "days_ahead": {"type": "integer", "description": "Number of days ahead to check (e.g., 7)"},
        "calendar_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Calendar IDs (default: ['primary'])",
            "optional": True,
            "nullable": True
        },
        "timezone": {
            "type": "string",
            "description": "IANA timezone for working hours and output (e.g., 'Europe/Berlin'). Default: 'UTC'",
            "optional": True,
            "nullable": True
        },
        "work_start_hour": {
            "type": "integer",
            "description": "Daily working window start hour (0-23). Default: 9",
            "optional": True,
            "nullable": True
        },
        "work_end_hour": {
            "type": "integer",
            "description": "Daily working window end hour (0-23). Default: 18",
            "optional": True,
            "nullable": True
        },
    }
    output_type = "object"
    access_token = ""

    def __init__(self, token):
        super().__init__(  # <-- REQUIRED so smolagents sets is_initialized, etc.
            name=self.name,
            description=self.description,
            inputs=self.inputs,
            output_type=self.output_type,
        )
        self.access_token = token


    def forward(
        self,
        days_ahead: int,
        calendar_ids: Optional[List[str]] = None,
        timezone: Optional[str] = None,        # <-- API surface kept the same...
        work_start_hour: int = 9,
        work_end_hour: int = 18,
    ) -> Dict[str, Any]:
    
        days_ahead = max(1, days_ahead)
        cal_ids = calendar_ids or ["primary"]
        tz_name = timezone or "UTC"             # <-- ...but immediately rename to avoid shadowing
        token = self.access_token
        if not token:
            return {"error": "Missing Google Calendar access token."}

        # Current time in UTC
        now_utc = dt.datetime.now(dt.timezone.utc)                 # <-- never pass a string tz
        time_min = now_utc.isoformat().replace("+00:00", "Z")
        time_max = (now_utc + dt.timedelta(days=days_ahead)).isoformat().replace("+00:00", "Z")

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": tz_name,                                   # Google FreeBusy field
            "items": [{"id": cid} for cid in cal_ids]
        }

        try:
            resp = requests.post(GOOGLE_FREEBUSY_URL, headers=_bearer_headers(token),
                                 data=json.dumps(body), timeout=20)
            resp.raise_for_status()
            fb = resp.json().get("calendars", {})

            # Collect & merge busy intervals (aware UTC datetimes)
            busy_all: List[Tuple[dt.datetime, dt.datetime]] = []
            for cal in fb.values():
                for b in cal.get("busy", []):
                    b_start = dt.datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
                    b_end   = dt.datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
                    busy_all.append((b_start, b_end))
            busy_merged = _merge_intervals(busy_all)

            # Build free windows per local day within working hours
            z = ZoneInfo(tz_name)
            results_by_day: Dict[str, Dict[str, Any]] = {}

            start_local_day = now_utc.astimezone(z).replace(hour=0, minute=0, second=0, microsecond=0)

            for d in range(days_ahead):
                day_local = start_local_day + dt.timedelta(days=d)
                day_start_local = day_local.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
                day_end_local   = day_local.replace(hour=work_end_hour,   minute=0, second=0, microsecond=0)

                # Convert working window to UTC
                day_start_utc = day_start_local.astimezone(dt.timezone.utc)
                day_end_utc   = day_end_local.astimezone(dt.timezone.utc)

                # Busy intervals that intersect this day's window
                day_busy: List[Tuple[dt.datetime, dt.datetime]] = []
                for b_start, b_end in busy_merged:
                    if b_end <= day_start_utc or b_start >= day_end_utc:
                        continue
                    day_busy.append((max(b_start, day_start_utc), min(b_end, day_end_utc)))

                day_busy = _merge_intervals(day_busy)
                day_free = _invert_busy_to_free(day_busy, day_start_utc, day_end_utc)

                def fmt_interval(dt_pair: Tuple[dt.datetime, dt.datetime]) -> Dict[str, str]:
                    s, e = dt_pair
                    return {
                        "start_local": s.astimezone(z).isoformat(),
                        "end_local":   e.astimezone(z).isoformat(),
                        "start_utc":   s.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                        "end_utc":     e.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                    }

                results_by_day[day_local.date().isoformat()] = {
                    "free": [fmt_interval(iv) for iv in day_free],
                    "busy": [fmt_interval(iv) for iv in day_busy],
                }

            return {
                "time_min_utc": time_min,
                "time_max_utc": time_max,
                "timezone": tz_name,
                "work_hours": {"start": work_start_hour, "end": work_end_hour},
                "availability_by_day": results_by_day,
            }

        except requests.exceptions.HTTPError as e:
            return {"error": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {e}"}



class GoogleCalendarCreateEventTool(Tool):
    name = "google_calendar_create_event"
    description = (
        "Create a calendar event only if there is no conflict. Checks FreeBusy for the given "
        "time window; if any conflict exists, returns a fallback with reason and does not create."
    )
    inputs = {
        "calendar_id": {"type": "string", "description": "Calendar ID (default: 'primary')", "optional": True, "nullable": True},
        "summary": {"type": "string", "description": "Event title"},
        "start_iso": {"type": "string", "description": "Event start in RFC3339 (e.g., '2025-09-25T14:00:00+02:00')"},
        "end_iso": {"type": "string", "description": "Event end in RFC3339 (must be after start)"},
        "timezone": {"type": "string", "description": "IANA timezone for the event (e.g., 'Europe/Berlin')"},
        "description": {"type": "string", "description": "Event description", "optional": True, "nullable": True},
        "location": {"type": "string", "description": "Location/address", "optional": True, "nullable": True},
        "attendees": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Attendee emails",
            "optional": True,
            "nullable": True
        },
        # "access_token": {
        #     "type": "string",
        #     "description": "OAuth 2.0 Bearer token. If omitted, uses GOOGLE_CALENDAR_ACCESS_TOKEN from globals.",
        #     "optional": True, 
        #     "nullable": True
        # }
    }
    output_type = "object"
    access_token = ""

    def __init__(self, token):
        super().__init__(  # <-- REQUIRED so smolagents sets is_initialized, etc.
            name=self.name,
            description=self.description,
            inputs=self.inputs,
            output_type=self.output_type,
        )
        self.access_token = token


    def forward(
        self,
        summary: str,
        start_iso: str,
        end_iso: str,
        timezone: str,
        calendar_id: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        cal_id = calendar_id or "primary"
        token = self.access_token or GOOGLE_CALENDAR_ACCESS_TOKEN
        if not token:
            return {"created": False, "error": "Missing Google Calendar access token."}

        # Parse to UTC for conflict check
        try:
            start_dt = dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            end_dt = dt.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            if end_dt <= start_dt:
                return {"created": False, "error": "end_iso must be after start_iso."}
        except Exception as e:
            return {"created": False, "error": f"Invalid datetime format: {e}"}

        # 1) FreeBusy conflict check
        fb_body = {
            "timeMin": start_dt.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "timeMax": end_dt.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "items": [{"id": cal_id}],
            "timeZone": timezone,
        }

        try:
            fb_resp = requests.post(GOOGLE_FREEBUSY_URL, headers=_bearer_headers(token), data=json.dumps(fb_body), timeout=20)
            fb_resp.raise_for_status()
            cal_busy = fb_resp.json().get("calendars", {}).get(cal_id, {}).get("busy", [])
            if cal_busy:
                return {
                    "created": False,
                    "conflict": True,
                    "reason": "Time window overlaps existing event(s).",
                    "conflicts": cal_busy
                }
        except requests.exceptions.RequestException as e:
            return {"created": False, "error": f"FreeBusy check failed: {e}"}

        event_body: Dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start_iso, "timeZone": timezone},
            "end": {"dateTime": end_iso, "timeZone": timezone},
        }
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": a} for a in attendees]

        try:
            events_url = GOOGLE_EVENTS_URL_TMPL.format(calendar_id=cal_id)
            create_resp = requests.post(events_url, headers=_bearer_headers(token), data=json.dumps(event_body), timeout=20)
            create_resp.raise_for_status()
            created = create_resp.json()
            return {
                "created": True,
                "event_id": created.get("id"),
                "htmlLink": created.get("htmlLink"),
                "summary": created.get("summary"),
                "start": created.get("start"),
                "end": created.get("end"),
            }
        except requests.exceptions.HTTPError as e:
            return {"created": False, "error": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
        except requests.exceptions.RequestException as e:
            return {"created": False, "error": f"Request failed: {e}"}
