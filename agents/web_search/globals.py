import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")
if not GOOGLE_API_KEY or not GOOGLE_MAPS_KEY:
    raise SystemExit("Please set GOOGLE_API_KEY and GOOGLE_MAPS_KEY in your environment.")
