import os
import json
import requests
from typing import List, Dict, Any, Optional

from .globals import *
from smolagents import Tool, CodeAgent
from smolagents.models import LiteLLMModel
from .tools import CombinedReservationSearchTool


PLACES_FIELDS = (
    "places.id,places.displayName,places.formattedAddress,places.websiteUri,"
    "places.nationalPhoneNumber,places.currentOpeningHours,places.rating,"
    "places.userRatingCount,places.priceLevel,places.types"
)


def build_agent() -> CodeAgent:
    """
    Minimal agent: only the CombinedReservationSearchTool is available.
    The model is instructed to call exactly one tool and return its raw JSON result.
    """
    model = LiteLLMModel(
        model_id="gemini/gemini-2.5-flash-lite",
        api_key=os.getenv("GOOGLE_API_KEY"),
    )

    tools = [CombinedReservationSearchTool()]

    return CodeAgent(tools=tools, model=model)

def search_places(search_term: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
    """
    Search for places using the specified search term.
    
    Args:
        search_term: What to search for (e.g., "hairdressers", "restaurants", "dentists")
        latitude: Optional latitude for location bias
        longitude: Optional longitude for location bias
    
    Returns:
        Dict with search results
    """
    # Use provided coordinates or get from IP
    if latitude is None or longitude is None:
        ipinfo = requests.get("https://ipinfo.io/json", timeout=10).json()
        lat, lon = map(float, ipinfo["loc"].split(","))
    else:
        lat, lon = latitude, longitude

    task = f"""You ONLY help by calling the 'search_and_reservations' tool exactly once.
    Do not write explanations or code.
    Return the tool's result as a JSON string. If the tool returns an array/dict,
    output exactly that JSON and nothing else. Find {search_term} near location {lat}, {lon}."""

    agent = build_agent()
    result = agent.run(task=task)

    if isinstance(result, (dict, list)):
        return result
    else:
        return {"error": "Invalid result format", "raw_result": str(result)}


class PlaceSearchAgent:
    """
    A reusable agent for searching places using Google Places API.
    Can be imported and used as a building block in other applications.
    """
    
    def __init__(self, default_latitude: Optional[float] = None, default_longitude: Optional[float] = None):
        """
        Initialize the search agent with optional default coordinates.
        
        Args:
            default_latitude: Default latitude for searches
            default_longitude: Default longitude for searches
        """
        self.default_lat = default_latitude
        self.default_lon = default_longitude
        self._agent = None
    
    def _get_agent(self) -> CodeAgent:
        """Lazy initialization of the agent"""
        if self._agent is None:
            self._agent = build_agent()
        return self._agent
    
    def search(self, search_term: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
        """
        Search for places using the specified search term.
        
        Args:
            search_term: What to search for (e.g., "hairdressers", "restaurants", "dentists")
            latitude: Optional latitude for location bias (uses default if not provided)
            longitude: Optional longitude for location bias (uses default if not provided)
        
        Returns:
            Dict with search results
        """
        # Use provided coordinates, then defaults, then IP location
        if latitude is None:
            latitude = self.default_lat
        if longitude is None:
            longitude = self.default_lon
            
        # Use provided coordinates or get from IP
        if latitude is None or longitude is None:
            ipinfo = requests.get("https://ipinfo.io/json", timeout=10).json()
            lat, lon = map(float, ipinfo["loc"].split(","))
        else:
            lat, lon = latitude, longitude

        task = f"""You ONLY help by calling the 'search_and_reservations' tool exactly once.
    Do not write explanations or code.
    Return the tool's result as a JSON string. If the tool returns an array/dict,
    output exactly that JSON and nothing else. Find {search_term} near location {lat}, {lon}."""

        agent = self._get_agent()  # <-- This is where _get_agent() actually runs!
        result = agent.run(task=task)

        if isinstance(result, (dict, list)):
            return result
        else:
            return {"error": "Invalid result format", "raw_result": str(result)}


# def main() -> None:
#     """Debug main function for testing the search agent"""
#     print("=== Testing PlaceSearchAgent ===")
    
#     # Test with PlaceSearchAgent class
#     agent = PlaceSearchAgent()
    
#     # Test searches
#     search_terms = ["hairdressers", "restaurants", "dentists"]
    
#     for term in search_terms:
#         print(f"\n--- Searching for {term} ---")
#         try:
#             result = agent.search(term)
#             print(f"Found {len(result) if isinstance(result, list) else 'N/A'} results")
#             print(f"Result type: {type(result)}")
#             if isinstance(result, dict) and "error" in result:
#                 print(f"Error: {result['error']}")
#             else:
#                 print("Success!")
#         except Exception as e:
#             print(f"Exception: {e}")
    
#     print("\n=== Testing search_places function ===")
    
#     # Test with standalone function
#     try:
#         result = search_places("gyms")
#         print(f"Function search successful: {type(result)}")
#     except Exception as e:
#         print(f"Function search failed: {e}")

# if __name__ == "__main__":
#     main()
