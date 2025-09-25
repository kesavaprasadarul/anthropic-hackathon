import os
import json
import requests
from typing import List, Dict, Any, Optional

from globals import *  # expects GOOGLE_API_KEY, PLACES_SEARCH_TEXT_URL, PLACES_FIELDS
from smolagents import Tool, CodeAgent
from smolagents.models import LiteLLMModel
from tools import CombinedReservationSearchTool


# Keep the Places field mask compact and focused on reservation-relevant bits
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
        api_key=os.getenv("GEMINI_KEY"),
    )

    tools = [CombinedReservationSearchTool()]

    # Strongly constrain the agent to: (1) call the tool once, (2) return JSON only.

    return CodeAgent(tools=tools, model=model)

BASE_TASK = (
    "You ONLY help by calling the 'search_and_reservations' tool exactly once. "
    "Do not write explanations or code. "
    "Return the tool's result as a JSON string. If the tool returns an array/dict, "
    "output exactly that JSON and nothing else. "
)

def main() -> None:
    # Rough location (you can replace this with user-provided lat/lon if you prefer)
    ipinfo = requests.get("https://ipinfo.io/json", timeout=10).json()
    lat, lon = map(float, ipinfo["loc"].split(","))

    task = BASE_TASK + f"Find hairdressers near location {lat}, {lon}"

    agent = build_agent()
    result = agent.run(task=task)

    if isinstance(result, (dict, list)):
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result)


if __name__ == "__main__":
    main()
