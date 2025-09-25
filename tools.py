import json
from smolagents import Tool
from typing import List, Dict, Any, Tuple, Optional
from globals import GOOGLE_API_KEY
import requests
import datetime as dt
from zoneinfo import ZoneInfo


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


class GooglePlacesSearchTool(Tool):
    name = "google_places_search"
    description = (
        "Search Google Places for various types of businesses or points of interest "
        "near a given lat/lng within a ~1km radius, ranked by popularity. "
        "Returns up to 10 results with key details."
    )
    inputs = {
        "latitude":  {"type": "number", "description": "Latitude of the user location"},
        "longitude": {"type": "number", "description": "Longitude of the user location"},
        "place_type": {"type": "string", "description": "The type of place to search for (e.g., 'cafe', 'park', 'museum')"},
        "radius": {"type": "string", "description": "Radius of search", "optional": True, "nullable": True}
    }
    output_type = "array"

    def forward(self, latitude: float, longitude: float, place_type: str, radius: Optional[str]) -> List[Dict[str, Any]]:
        """
        Performs a nearby search for a given place type using the Google Places API.
        """
        radius = radius if radius != 0 else 1000
        payload = {
            "includedTypes": [place_type],
            "locationRestriction": {
                "circle": {"center": {"latitude": latitude, "longitude": longitude}, "radius": radius}
            },
            "rankPreference": "POPULARITY",
            "maxResultCount": 10,
            "keyword": "German",
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": PLACES_FIELDS
        }
        
        try:
            resp = requests.post(
                PLACES_SEARCH_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
            places = data.get("places", [])
            
            if not places:
                return [
                    {"message": f"No {place_type}s found near the specified location."}
                ]

            return places
            
        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP Error: {e.response.status_code} - {e.response.text}"
            return [{"error": error_message}]
        except requests.exceptions.RequestException as e:
            return [{"error": f"Request failed: {e}"}]


class GooglePlacesSearchTextTool(Tool):
    name = "google_places_search_text"
    description = (
        "Search Google Places using a free-form text query (e.g., 'best pizza near me'). "
        "Optionally bias by lat/lng and radius. Returns up to 10 results ranked by popularity."
    )
    inputs = {
        "text_query": {"type": "string", "description": "Free-form search text (e.g., 'best sushi', 'vegan brunch')"},
        "latitude": {"type": "number", "description": "Latitude for location bias", "optional": True, "nullable": True},
        "longitude": {"type": "number", "description": "Longitude for location bias", "optional": True, "nullable": True},
        "radius": {"type": "integer", "description": "Radius in meters for location bias (default 1000)", "optional": True, "nullable": True},
    }
    output_type = "array"

    def forward(
        self,
        text_query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "textQuery": text_query,
            "maxResultCount": 20,
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
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": PLACES_FIELDS
        }
        try:
            resp = requests.post(
                PLACES_SEARCH_TEXT_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            places = data.get("places", [])
            if not places:
                return [{"message": "No places matched the text query."}]
            return places
        except requests.exceptions.HTTPError as e:
            return [{"error": f"HTTP Error: {e.response.status_code} - {e.response.text}"}]
        except requests.exceptions.RequestException as e:
            return [{"error": f"Request failed: {e}"}]


class BookingInstructionsTool(Tool):
    name = "reservation_instructions"
    description = (
        "Given a place dict (from Google Places), determine how to reserve: "
        "website booking, phone call, or generic instructions."
    )
    inputs = {
        "place": {"type": "object", "description": "Fields like name, website, phone, address"}
    }
    # Return is a string
    output_type = "string"

    def forward(self, place: Dict[str, Any]) -> str:
        name = place.get("name") or "the place"
        website = place.get("website")
        phone = place.get("phone")

        if website:
            return (
                f"Visit {website} and look for a 'Reserve' or 'Book a table' button. "
                f"If online booking is unavailable, call {phone or 'the venue'} to reserve."
            )
        if phone:
            return (
                f"Call {phone} and request a table at {name}. "
                f"Have your party size, date, and time ready."
            )
        address = place.get("address")
        return (
            f"No website or phone found. Search the place name online for a booking link. "
            f"Alternatively, visit in person{f' at {address}' if address else ''} to inquire about reservations."
        )

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
        "access_token": {
            "type": "string",
            "description": "OAuth 2.0 Bearer token. If omitted, uses GOOGLE_CALENDAR_ACCESS_TOKEN from globals.",
            "optional": True,
            "nullable": True
        }
    }
    output_type = "object"

    def forward(
        self,
        days_ahead: int,
        calendar_ids: Optional[List[str]] = None,
        timezone: Optional[str] = None,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        cal_ids = calendar_ids or ["primary"]
        tz = timezone or "UTC"
        token = access_token
        if not token:
            return {"error": "Missing Google Calendar access token."}

        now_utc = dt.datetime.now(timezone_module := timezone if False else timezone)  # placeholder to avoid name clash
        now_utc = dt.datetime.now(timezone.utc)
        time_min = now_utc.isoformat().replace("+00:00", "Z")
        time_max = (now_utc + timedelta(days=days_ahead)).isoformat().replace("+00:00", "Z")

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": tz,
            "items": [{"id": cid} for cid in cal_ids]
        }

        try:
            resp = requests.post(GOOGLE_FREEBUSY_URL, headers=_bearer_headers(token), data=json.dumps(body), timeout=20)
            resp.raise_for_status()
            fb = resp.json().get("calendars", {})

            # Collect & merge busy intervals across calendars (in UTC)
            busy_all: List[Tuple[dt.datetime, dt.datetime]] = []
            for cal in fb.values():
                for b in cal.get("busy", []):
                    b_start = dt.datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
                    b_end = dt.datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
                    busy_all.append((b_start, b_end))
            busy_merged = _merge_intervals(busy_all)

            # Build free windows per local day within working hours
            z = ZoneInfo(tz)
            results_by_day: Dict[str, Dict[str, Any]] = {}
            start_local_day = dt.datetime.now(timezone.utc).astimezone(z).replace(hour=0, minute=0, second=0, microsecond=0)

            for d in range(days_ahead):
                day_local = start_local_day + timedelta(days=d)
                day_start_local = day_local.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
                day_end_local = day_local.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)

                # Convert working window to UTC
                day_start_utc = day_start_local.astimezone(timezone.utc)
                day_end_utc = day_end_local.astimezone(timezone.utc)

                # Busy intervals that touch this day window
                day_busy = []
                for b_start, b_end in busy_merged:
                    if b_end <= day_start_utc or b_start >= day_end_utc:
                        continue
                    day_busy.append((max(b_start, day_start_utc), min(b_end, day_end_utc)))

                day_busy = _merge_intervals(day_busy)
                day_free = _invert_busy_to_free(day_busy, day_start_utc, day_end_utc)

                def fmt_interval(dt_pair: Tuple[datetime, datetime]) -> Dict[str, str]:
                    s, e = dt_pair
                    return {
                        "start_local": s.astimezone(z).isoformat(),
                        "end_local": e.astimezone(z).isoformat(),
                        "start_utc": s.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                        "end_utc": e.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                    }

                results_by_day[day_local.date().isoformat()] = {
                    "free": [fmt_interval(iv) for iv in day_free],
                    "busy": [fmt_interval(iv) for iv in day_busy],
                }

            return {
                "time_min_utc": time_min,
                "time_max_utc": time_max,
                "timezone": tz,
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
        "access_token": {
            "type": "string",
            "description": "OAuth 2.0 Bearer token. If omitted, uses GOOGLE_CALENDAR_ACCESS_TOKEN from globals.",
            "optional": True, 
            "nullable": True
        }
    }
    output_type = "object"

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
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        cal_id = calendar_id or "primary"
        token = access_token or GOOGLE_CALENDAR_ACCESS_TOKEN
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
