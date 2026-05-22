import os
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
YOUTUBE_CLIENT_SECRET_FILE = os.environ.get("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")
YOUTUBE_TOKEN_FILE = os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token.json")

# ── Models (same SDK pattern as affirmation agent) ────────────────────────────
BRAIN_MODEL = "gemini-2.5-flash"
MUSIC_MODEL = "lyria-realtime-exp"
IMAGEN_MODEL = "gemini-3-pro-image-preview"   # same model affirmation agent uses
VEO_MODEL = "veo-3.0-generate-preview"

# ── Content rotation ──────────────────────────────────────────────────────────
RAGAS = [
    {"raga": "Yaman",        "mood": "peaceful, uplifting, evening calm"},
    {"raga": "Bhairavi",     "mood": "devotional, melancholic, deep surrender"},
    {"raga": "Darbari Kanada","mood": "majestic, contemplative, late night depth"},
    {"raga": "Bhupali",      "mood": "serene, hopeful, early evening"},
    {"raga": "Chandrakauns", "mood": "mysterious, meditative, midnight"},
    {"raga": "Yaman Kalyan", "mood": "romantic, gentle, dusk"},
    {"raga": "Bageshri",     "mood": "longing, introspective, late night"},
]
INSTRUMENTS = ["sitar", "bansuri flute", "sarod", "santoor", "veena"]
USE_CASES = [
    "deep sleep",
    "study and focus",
    "stress relief and anxiety",
    "morning meditation",
    "yoga and breathwork",
    "relaxation after work",
]
VISUAL_STYLES = ["mughal_miniature", "cinematic_photorealistic"]

# ── Video format ──────────────────────────────────────────────────────────────
MUSIC_DURATION_SEC = 180        # Lyria generates ~3-min clips
VIDEO_LOOPS = 4                 # 3 min × 4 = 12 min final video
VEO_CLIP_SEC = 8

# ── Output paths ──────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

def today_index() -> int:
    """Day-of-year index for cycling through ragas/instruments/use_cases."""
    return (date.today().toordinal()) % len(RAGAS)
