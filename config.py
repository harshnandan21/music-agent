import os
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
YOUTUBE_CLIENT_SECRET_FILE = os.environ.get("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")
YOUTUBE_TOKEN_FILE = os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token.json")

# ── Models ────────────────────────────────────────────────────────────────────
BRAIN_MODEL   = "gemini-2.5-flash"
MUSIC_MODEL   = "lyria-realtime-exp"
IMAGEN_MODEL  = "gemini-3-pro-image-preview"
VEO_MODEL     = "veo-3.0-generate-preview"

# ── Weekly schedule — SINGLE SOURCE OF TRUTH for every post ──────────────────
#
# Every field here controls what gets generated. Edit this dict to customise
# any day without touching any other file.
#
# Required fields
#   raga              Raga name (passed to Gemini + thumbnail)
#   raga_mood         Emotional description fed to Gemini for music direction
#   instruments       List — single / duo / trio; drives music + thumbnail line
#   use_case          Viewer benefit (study, sleep, etc.)
#   theme             One-line creative concept for the whole post
#   music_hints       Detailed playing style guidance for Lyria prompt
#   image_hints       Detailed scene description for Madhubani image prompt
#
# Optional overrides — set to None to let Gemini decide, or fill in to lock
#   hz_frequency      e.g. "432Hz" — baked into title + music prompt if set
#   title             Exact YouTube title (≤70 chars); None = Gemini writes it
#   thumbnail_hook    2-4 ALL-CAPS words shown large on thumbnail
#   thumbnail_instr   Instrument & Raga line on thumbnail middle
#   thumbnail_tagline 6-10 word benefit statement on thumbnail bottom strip
#
WEEKLY_SCHEDULE = {
    0: {  # Monday — deep focus for the work week
        "raga":        "Chandrakauns",
        "raga_mood":   "mysterious, meditative, midnight — each note lands with deliberate gravity",
        "instruments": ["veena", "tabla"],
        "use_case":    "study and focus",
        "theme":       "Midnight scholar's lamp — absolute stillness, mind locked in deep work",
        "music_hints": (
            "Veena leading with haunting slow alap, tabla entering softly after 90 seconds. "
            "Komal gandhar and komal nishad held long. 70 BPM inner pulse. "
            "Feel of laser-focus, each phrase a thought completing itself. No distraction, no hurry."
        ),
        "image_hints": (
            "Scholar's corner lit by an oil lamp glowing warm orange, veena and tabla "
            "beside a lotus-patterned mat, full moon outside a geometric window, "
            "peacock perched on the windowsill, intricate fish-border framing the scene, "
            "deep indigo and saffron palette."
        ),
        # ── overrides ────────────────────────────────────────────────────────
        "hz_frequency":       "741Hz",
        "title":              None,
        "thumbnail_hook":     "MIDNIGHT FOCUS",
        "thumbnail_instr":    "VEENA & TABLA · RAAG CHANDRAKAUNS",
        "thumbnail_tagline":  "Dissolve Brain Fog & Think With Clarity",
    },

    1: {  # Tuesday — mid-week unwind
        "raga":        "Yaman Kalyan",
        "raga_mood":   "romantic, gentle, dusk — the day's weight slowly dissolving",
        "instruments": ["sitar", "bansuri flute"],
        "use_case":    "relaxation after work",
        "theme":       "Sitar and flute in evening dialogue — city noise fading into calm water",
        "music_hints": (
            "Sitar and bansuri in gentle call-and-response. Sitar sets the melodic foundation, "
            "bansuri answers with breathy long tones. Teentaal at 80 BPM, light tabla. "
            "Warm meend glides on sitar, flute phrases that feel like a long exhale. "
            "Mood: relief, soft joy, the body unclenching after a long day."
        ),
        "image_hints": (
            "Lakeside scene at dusk, sitar player and bansuri player facing each other "
            "on a lotus-adorned carpet, mango tree canopy above, diyas reflected in still water, "
            "peacocks and deer in golden light, vibrant saffron-to-teal sky."
        ),
        # ── overrides ────────────────────────────────────────────────────────
        "hz_frequency":       None,
        "title":              None,
        "thumbnail_hook":     "AFTER WORK CALM",
        "thumbnail_instr":    "SITAR & BANSURI · RAAG YAMAN KALYAN",
        "thumbnail_tagline":  "Release Office Stress & Reset Your Mind",
    },

    2: {  # Wednesday — hump-day stress release
        "raga":        "Bageshri",
        "raga_mood":   "longing, introspective, late night — emotions quietly surfacing and releasing",
        "instruments": ["bansuri flute"],
        "use_case":    "stress relief and anxiety",
        "theme":       "Lone bansuri in monsoon rain — every breath releases what you have been holding",
        "music_hints": (
            "Solo bansuri, breathy and intimate. Vilambit at 55 BPM. "
            "Long held komal notes that sigh and resolve, like exhaling weeks of tension. "
            "Soft rain texture under the tanpura drone. No tabla until 2.5 minutes. "
            "Mood: melting, releasing, being held by the music itself."
        ),
        "image_hints": (
            "Arched doorway with stylized monsoon rain falling outside, bansuri resting "
            "on an embroidered cushion, candle burning beside a lotus flower, "
            "rain droplets drawn as teardrops on the geometric border, "
            "deep teal and rose palette, peacock sheltering under mango leaves."
        ),
        # ── overrides ────────────────────────────────────────────────────────
        "hz_frequency":       "528Hz",
        "title":              None,
        "thumbnail_hook":     "STRESS DETOX",
        "thumbnail_instr":    "BANSURI FLUTE · RAAG BAGESHRI",
        "thumbnail_tagline":  "Monsoon Rain Flute to Calm Your Nervous System",
    },

    3: {  # Thursday — pre-weekend deep rest
        "raga":        "Yaman",
        "raga_mood":   "peaceful, uplifting, evening calm — light releasing into stillness",
        "instruments": ["santoor", "tanpura"],
        "use_case":    "deep sleep",
        "theme":       "Santoor crystals over tanpura drone — 432Hz, body melting into rest",
        "music_hints": (
            "Santoor with pure crystal-hammer strokes tuned to 432Hz. Vilambit at 50 BPM. "
            "Tanpura drone in low register as unbroken foundation. "
            "Long silences between santoor phrases — the silence is part of the music. "
            "Progressively sparser after 2 minutes. "
            "Mood: drifting, weightless, each phrase further from wakefulness."
        ),
        "image_hints": (
            "Open terrace at twilight, santoor lying on a silk cloth beside a glowing tanpura, "
            "crescent moon and stars drawn in geometric spirals, "
            "lotus pond below with fish and birds settling for the night, "
            "soft rose-violet and ivory palette."
        ),
        # ── overrides ────────────────────────────────────────────────────────
        "hz_frequency":       "432Hz",
        "title":              None,
        "thumbnail_hook":     "DEEP SLEEP NOW",
        "thumbnail_instr":    "SANTOOR & TANPURA · RAAG YAMAN",
        "thumbnail_tagline":  "432Hz Music to Fall Asleep Fast & Stay Asleep",
    },

    4: {  # Friday — energetic start to the weekend
        "raga":        "Bhupali",
        "raga_mood":   "serene, hopeful, expansive — pentatonic openness, bright and alive",
        "instruments": ["sitar", "sarod", "tabla"],
        "use_case":    "yoga and breathwork",
        "theme":       "Three instruments, one sunrise — body, breath, and rhythm awakening together",
        "music_hints": (
            "Sitar, sarod, and tabla in full sunrise energy. Sitar leads the melody, "
            "sarod adds resonant depth, tabla drives steady teentaal at 90 BPM. "
            "Bright pentatonic phrases that expand and breathe. "
            "Each 16-beat cycle mirrors an inhale-exhale breath sequence. "
            "Mood: alive, expansive, body and cosmos in harmony."
        ),
        "image_hints": (
            "Three musicians — sitar player, sarod player, tabla player — seated on "
            "a mountain terrace at sunrise, golden rays and stylized birds radiating outward, "
            "lotus flowers and deer in the foreground, bold geometric sun motif above, "
            "vibrant red, gold and forest-green palette, intricate elephant border."
        ),
        # ── overrides ────────────────────────────────────────────────────────
        "hz_frequency":       None,
        "title":              None,
        "thumbnail_hook":     "MORNING ENERGY",
        "thumbnail_instr":    "SITAR, SAROD & TABLA · RAAG BHUPALI",
        "thumbnail_tagline":  "Breathe. Move. Awaken. Indian Classical for Yoga",
    },

    5: {  # Saturday — late-night weekend depth
        "raga":        "Darbari Kanada",
        "raga_mood":   "majestic, contemplative, late-night gravity — heavy with meaning",
        "instruments": ["sitar", "bansuri flute", "tabla"],
        "use_case":    "late night relaxation",
        "theme":       "Midnight trio — sitar, flute, and tabla in the emperor's private hours",
        "music_hints": (
            "Sitar leads with weighty alap, bansuri answers with midnight phrases, "
            "tabla enters softly at 3 minutes with a slow dadra. "
            "45 BPM inner pulse. Deep komal rishab and komal gandhar with heavy meend. "
            "Mood: majestic stillness, thoughts settling like sediment, profound late-night depth."
        ),
        "image_hints": (
            "Night garden with three musicians under a flowering tree — sitar player, "
            "bansuri player, tabla player — full moon glowing overhead, "
            "peacocks and deer listening in the shadows, oil lamps in a semicircle, "
            "deep indigo and gold palette, stylized star-filled sky with mandala moon."
        ),
        # ── overrides ────────────────────────────────────────────────────────
        "hz_frequency":       "396Hz",
        "title":              None,
        "thumbnail_hook":     "MIDNIGHT CALM",
        "thumbnail_instr":    "SITAR, BANSURI & TABLA · RAAG DARBARI",
        "thumbnail_tagline":  "Saturday Night Deep Relaxation for the Soul",
    },

    6: {  # Sunday — devotional morning reset
        "raga":        "Bhairavi",
        "raga_mood":   "devotional, melancholic, surrendered — the most emotionally complete raga",
        "instruments": ["bansuri flute", "tanpura"],
        "use_case":    "morning meditation",
        "theme":       "Bansuri over tanpura at the Ganges — Sunday surrender, week washing away",
        "music_hints": (
            "Bansuri warm and intimate over a continuous tanpura drone. "
            "Slow vilambit at 60 BPM turning to madhya laya. "
            "Bhairavi's all-komal notes creating profound emotional depth and surrender. "
            "Mood: washing clean, openness, readiness for the new week."
        ),
        "image_hints": (
            "Bansuri player seated at a river's edge at dawn, tanpura lying beside them "
            "on a lotus-patterned mat, stylized rising sun with concentric golden rings, "
            "lotus flowers on the water, birds flying in formation above, "
            "saffron and gold palette, geometric fish-and-wave border."
        ),
        # ── overrides ────────────────────────────────────────────────────────
        "hz_frequency":       None,
        "title":              None,
        "thumbnail_hook":     "SUNDAY RESET",
        "thumbnail_instr":    "BANSURI & TANPURA · RAAG BHAIRAVI",
        "thumbnail_tagline":  "Start Your Week with Devotion & Inner Peace",
    },
}

# ── Content strategy seeds (injected into Gemini brain prompt) ───────────────
CONTENT_SEEDS = {
    "outcome_hooks": [
        "Mental Clarity", "Brain Fog Gone", "Stress Detox", "Deep Focus",
        "Anxiety Reset", "Nervous System Calm", "Emotional Detox", "Mind Reset",
        "Stop Overthinking", "Morning Clarity", "Work Focus", "Inner Stillness",
        "Sleep Fast", "Wake Up Calm", "Dissolve Tension",
    ],
    "atmosphere_hooks": [
        "Monsoon Rain", "Temple at Dawn", "Candlelight", "Midnight Stillness",
        "Ganges Sunrise", "Kerala Forest", "Mountain Morning", "Rain on Leaves",
        "Desert Night", "River Fog",
    ],
    "title_patterns": [
        "{outcome} {emoji} {instruments} | {secondary_benefit} | Raga {raga}",
        "{hz} {instruments} | {outcome} | {use_case} | Raga {raga}",
        "{atmosphere} {emoji} {instruments} for {outcome} | Indian Raga Therapy",
        "Can't {problem}? {instruments} & Raga {raga} That Actually Works",
        "{atmosphere} × {instruments} | {outcome}",
        "Stop {problem}: {instruments} Music for {use_case} | Raga {raga}",
    ],
    "hook_phrases": [
        # Stress / anxiety
        "Your stress ends here.",
        "For the next 2 hours, nothing is your problem.",
        "You don't need to be okay right now. Just be here.",
        "Ancient strings. Sparse beats. Deep healing.",
        # Morning / energy
        "Some mornings deserve sitar, not scrolling.",
        "Before the world begins — meet yourself.",
        "Let the Himalayas start your day.",
        # Instrument-focused
        "The bansuri speaks what your heart has been holding.",
        "One breath. One note. One moment of peace.",
        # Sleep / night
        "Let your mind land somewhere soft tonight.",
        "The raga knows. Just listen.",
    ],
    "hashtag_tiers": {
        "big":    ["#meditationmusic", "#indianclassicalmusic", "#healingmusic", "#stressrelief", "#sleepmusic"],
        "medium": ["#sitarmusic", "#bansuriflute", "#ragamusic", "#soundhealing", "#indianambient"],
        "niche":  ["#ragatherapy", "#madhubani", "#dhundetox"],
        "hindi":  ["#तनावमुक्ति", "#मनशांति"],
    },
    "avoid_generic": [
        "Relaxing Music", "Healing Music", "Indian Music", "Classical Music", "Meditation Music",
    ],
}

# ── Madhubani visual style (shared by image + thumbnail prompts) ──────────────
MADHUBANI_STYLE = (
    "Madhubani folk painting style from Mithila, Bihar, India. "
    "16:9 widescreen format. "
    "Flat 2D perspective with bold hand-drawn black outlines. "
    "Hand-painted texture on aged parchment or natural fabric. "
    "Vibrant natural pigments: deep red, saffron yellow, peacock teal, forest green, "
    "ivory white, turmeric gold. "
    "Characteristic nature motifs: peacocks, lotus flowers, mango leaves, fish, deer, birds. "
    "Intricate geometric and floral borders with elephants and paisley. "
    "No text, no watermarks, no 3D shading, no photorealism, no Western art influence."
)

# ── Cinematic photo-realistic style (for use cases that suit real-world scenes) ─
CINEMATIC_STYLE = (
    "Cinematic photo-realistic 16:9 scene. "
    "Ultra-detailed 8K photography quality. No people, no text, no watermarks. "
    "Instruments arranged naturally — sitar / bansuri / tabla on a silk cloth or stone surface. "
    "Atmospheric lighting: candlelight, moonlight, or golden sunrise. "
    "Natural elements: incense smoke, mist, rain droplets, marigold flowers. "
    "Warm amber and deep midnight blue color palette. "
    "Loop-friendly composition: animatable smoke, flame, or mist in foreground."
)

# ── Video animation elements by scene type (for Veo/video_prompt guidance) ────
VIDEO_ANIMATION_GUIDE = (
    "Madhubani night scene: stars twinkling 2%, mandala rotating 1%, lotus swaying 5%, fish swimming 10%. "
    "Temple altar scene: candle flames 5%, incense smoke rising 80%, diya glow 5%. "
    "Mountain/mist scene: mist drifting 15%, prayer flags fluttering 10%, butter lamp 5%. "
    "Rain scene: rain falling 100%, smoke rising 80%, lamp glow 5%. "
    "ALWAYS: static camera, no zoom, no pan, identical first and last frame, seamless 8-second loop."
)

# ── YouTube keyword banks (for tags and description guidance) ─────────────────
YOUTUBE_KEYWORDS = {
    "english": [
        "stress detox", "sitar music", "tabla music", "indian classical music",
        "raga therapy", "meditation music", "healing music", "stress relief",
        "anxiety relief", "sleep music", "nervous system reset", "sound healing",
        "calming music", "overthinking relief", "brain fog relief", "mental detox",
        "deep relaxation", "inner peace", "bansuri music", "flute music",
        "432hz", "chakra healing", "morning meditation",
    ],
    "hinglish": [
        "stress kam karne wala music", "mann shant karne ka sangeet",
        "chinta dur karne wala music", "neend ke liye music",
        "dimag shant karne wala music", "sukoon dene wala music",
    ],
}

# ── Video format ──────────────────────────────────────────────────────────────
MUSIC_DURATION_SEC = 180
VIDEO_LOOPS        = 4
VEO_CLIP_SEC       = 8

# ── FFmpeg ────────────────────────────────────────────────────────────────────
# Shotcut ships ffmpeg.exe but not ffprobe. We add its dir to PATH so all
# subprocess calls to "ffmpeg" resolve without full paths.
FFMPEG_DIR = r"C:\Program Files\Shotcut"
if FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# ── Output paths ──────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def today_schedule() -> dict:
    """Return today's schedule entry (0=Monday … 6=Sunday)."""
    return WEEKLY_SCHEDULE[date.today().weekday()]


def format_instruments(instruments: list) -> str:
    """'sitar' | 'sitar & bansuri' | 'sitar, sarod & tabla'"""
    if len(instruments) == 1:
        return instruments[0]
    if len(instruments) == 2:
        return f"{instruments[0]} & {instruments[1]}"
    return f"{', '.join(instruments[:-1])} & {instruments[-1]}"
