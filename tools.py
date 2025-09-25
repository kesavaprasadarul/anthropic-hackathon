import json
from smolagents import Tool
from typing import List, Dict, Any
from globals import GOOGLE_API_KEY
import requests

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACES_FIELDS = (
    "places.id,places.displayName,places.rating,places.userRatingCount,places.priceLevel,"
    "places.formattedAddress,places.servesVegetarianFood,places.nationalPhoneNumber,"
    "places.websiteUri,places.businessStatus,places.currentOpeningHours"
)

PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/"


class GooglePlacesTool(Tool):
    name = "google_places_search"
    description = (
        "Search Google Places for restaurants near a lat/lng within a ~1km radius, "
        "ranked by popularity; returns up to 10 with key details."
    )
    # Use JSON-schema-like strings for types
    inputs = {
        "latitude":  {"type": "number", "description": "Latitude of the user location"},
        "longitude": {"type": "number", "description": "Longitude of the user location"},
    }
    # Return is a list → use 'array'
    output_type = "array"

    def forward(self, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        payload = {
            "includedTypes": ["restaurant"],
            "locationRestriction": {
                "circle": {"center": {"latitude": latitude, "longitude": longitude}, "radius": 1000}
            },
            "rankPreference": "POPULARITY",
            "maxResultCount": 10
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": PLACES_FIELDS
        }
        resp = requests.post(PLACES_SEARCH_URL, headers=headers, data=json.dumps(payload), timeout=20)
        resp.raise_for_status()
        data = resp.json()
        places = data.get("places", [])
        return [
            {
                "id": p.get("id"),
                "name": (p.get("displayName") or {}).get("text"),
                "rating": p.get("rating"),
                "reviews": p.get("userRatingCount"),
                "priceLevel": p.get("priceLevel"),
                "address": p.get("formattedAddress"),
                "servesVegetarianFood": p.get("servesVegetarianFood"),
                "phone": p.get("nationalPhoneNumber"),
                "website": p.get("websiteUri"),
                "businessStatus": p.get("businessStatus"),
                "openingHours": p.get("currentOpeningHours"),
            }
            for p in places
        ]

class ReservationInstructionsTool(Tool):
    name = "reservation_instructions"
    description = (
        "Given a restaurant dict (from Google Places), determine how to reserve: "
        "website booking, phone call, or generic instructions."
    )
    inputs = {
        "restaurant": {"type": "object", "description": "Restaurant fields like name, website, phone, address"}
    }
    # Return is a string
    output_type = "string"

    def forward(self, restaurant: Dict[str, Any]) -> str:
        name = restaurant.get("name") or "the restaurant"
        website = restaurant.get("website")
        phone = restaurant.get("phone")

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
        address = restaurant.get("address")
        return (
            f"No website or phone found. Search the restaurant name online for a booking link. "
            f"Alternatively, visit in person{f' at {address}' if address else ''} to inquire about reservations."
        )
