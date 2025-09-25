import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")
if not GOOGLE_API_KEY:
    raise SystemExit("Please set GOOGLE_API_KEY in your environment.")