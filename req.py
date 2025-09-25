
import os
import json
import time
import requests
from typing import List, Dict, Any, Optional

from globals import *
from smolagents import Tool, CodeAgent
from smolagents.models import LiteLLMModel
from tools import GooglePlacesTool, ReservationInstructionsTool

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
        model_id="gemini/gemini-2.5-flash",
        api_key=os.getenv("GEMINI_KEY"),
    )
    tools = [GooglePlacesTool(), ReservationInstructionsTool()]
    return CodeAgent(tools=tools, model=model)



def main() -> None:

    ipinfo = requests.get("https://ipinfo.io/json").json()
    lat, lon = map(float, ipinfo["loc"].split(","))

    system_prompt = (
        "You are an assistant that helps users discover restaurants near them and explains "
        "how to reserve a table. Always return concise, actionable steps."
    )

    agent = build_agent()

    places: List[Dict[str, Any]] = agent.run(
        task="Find the top 10 restaurants within 1km and return structured json",
    )
    with open("places.json", "w", encoding="utf-8") as f:
        json.dump(places, f, indent=4, ensure_ascii=False)
    if isinstance(places, str):
        try:
            places = json.loads(places)
        except Exception:
            raise SystemExit("Agent did not return JSON. Please try again.")

    print(places)


if __name__ == "__main__":
    main()

