
import os
import json
import time
import requests
from typing import List, Dict, Any, Optional

from globals import *
from smolagents import Tool, CodeAgent
from smolagents.models import LiteLLMModel
from tools import GooglePlacesSearchTool, BookingInstructionsTool, GoogleCalendarCreateEventTool, GoogleCalendarAvailabilityTool, GooglePlacesSearchTextTool

details_headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": GOOGLE_API_KEY,
    "X-Goog-FieldMask": (
        "id,displayName,formattedAddress,googleMapsUri,"
        "reservable,websiteUri,internationalPhoneNumber,nationalPhoneNumber,"
        "currentOpeningHours,rating,userRatingCount,priceLevel"
    )
}


def build_agent() -> CodeAgent:
    model = LiteLLMModel(
        model_id="gemini/gemini-2.5-flash-lite",
        api_key=os.getenv("GEMINI_KEY"),
    )
    tools = [GooglePlacesSearchTextTool(), BookingInstructionsTool()]
    return CodeAgent(tools=tools, model=model)



def main() -> None:

    ipinfo = requests.get("https://ipinfo.io/json").json()
    lat, lon = map(float, ipinfo["loc"].split(","))

    task = (
        f"""
        You are an assistant that helps users make reservations of some appointments to places nearby,
        like a restaurant, a hairdresser's, cinema etc.

        The user is located approximately in {lat}, {lon}. You have tools to find the hairdressers nearby.

        In the radius of 2 km of the user, find restaurants with German cuisine.
        Choose one restaurant and output instructions on
        how to make the reservation. If there is an option to make a reservation online, do it.

        Use only the tools available and dont add any code processing of the output.

        In the end, return the name of the place, the booking phone and/or website, as well as the list of available times for booking.

        Also, add the booking
        """
    )
    

    agent = build_agent()

    places: List[Dict[str, Any]] = agent.run(
        task=task,
    )
    # if isinstance(places, str):
    #     try:
    #         places = json.loads(places)
    #     except Exception:
    #         raise SystemExit("Agent did not return JSON. Please try again.")


if __name__ == "__main__":
    main()

