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

# ── 20-Day Content Calendar — SINGLE SOURCE OF TRUTH for every post ──────────
#
# Cycles via date.today().toordinal() % 20 — repeats every 20 days.
# 20 unique ragas · 12 instruments (sitar, bansuri, tabla, tanpura, sarangi,
# harmonium, veena, sarod, shehnai, pakhawaj, mridangam, santoor) ·
# mix of solos, duos, trios.
#
# Required fields
#   raga              Raga name
#   thaat             Parent scale system (fed to Suno style tags)
#   raga_mood         Emotional description fed to Gemini
#   instruments       List — drives music + thumbnail line
#   use_case          Viewer benefit
#   theme             One-line creative concept
#   music_hints       Playing style guidance for Lyria + Suno
#   image_hints       Scene description for Madhubani image prompt
#   suno_lyrics_style One of: sleep / morning / focus / stress / midnight
#
# Optional overrides — set to None to let Gemini decide
#   hz_frequency / title / thumbnail_hook / thumbnail_instr / thumbnail_tagline
#
CONTENT_CALENDAR = {
    0: {  # Chandrakauns — Veena + Tabla — Deep Focus
        "raga":        "Chandrakauns",
        "thaat":       "Bhairavi",
        "raga_mood":   "mysterious, meditative, midnight — each note lands with deliberate gravity",
        "instruments": ["veena", "tabla"],
        "use_case":    "study and deep focus",
        "theme":       "Ancient veena in midnight silence — brain fog dissolves, thoughts crystallize in komal stillness",
        "music_hints": (
            "Veena leading with haunting slow alap, each note placed with deliberate weight. "
            "Komal gandhar and komal nishad held long with natural decay. "
            "Tabla entering softly after 90 seconds with sparse teentaal at 65 BPM. "
            "Laser-focus quality — each phrase a thought completing itself. "
            "No distraction, no hurry, wide silence between each phrase."
        ),
        "image_hints": (
            "Scholar's corner lit by an oil lamp glowing warm orange, ancient veena resting "
            "beside a lotus-patterned mat, full moon outside a geometric latticed window, "
            "peacock perched silently on the windowsill, fish-border framing the entire scene, "
            "deep indigo and saffron palette, intricate Madhubani geometric star-ceiling."
        ),
        "hz_frequency":      "741Hz",
        "title":             None,
        "thumbnail_hook":    "MIND WON'T FOCUS?",
        "thumbnail_instr":   "VEENA & TABLA · RAAG CHANDRAKAUNS",
        "thumbnail_tagline": "Dissolve Brain Fog & Think With Clarity",
        "playlist":          "focus",
        "suno_lyrics_style": "focus",
    },

    1: {  # Yaman Kalyan — Sitar + Bansuri + Tabla — Stress Relief
        "raga":        "Yaman Kalyan",
        "thaat":       "Kalyan",
        "raga_mood":   "romantic, gentle, dusk — the day's weight slowly dissolving into evening warmth",
        "instruments": ["sitar", "bansuri", "tabla"],
        "use_case":    "evening cortisol drop and stress relief",
        "theme":       "Sitar and bansuri at dusk — call-and-response trio dissolving cortisol, unclenching the body",
        "music_hints": (
            "Sitar sets melodic foundation, bansuri answers with breathy long tones in call-and-response. "
            "Tabla enters at 2 minutes with gentle teentaal at 80 BPM. "
            "Warm meend glides on sitar, flute phrases feel like a long exhale. "
            "Mood: relief, soft joy, the body unclenching after a long day."
        ),
        "image_hints": (
            "Lakeside scene at dusk, sitar player and bansuri player facing each other "
            "on a lotus-adorned carpet, tabla player beside them, mango tree canopy above, "
            "diyas reflected in still water, peacocks and deer in golden light, "
            "vibrant saffron-to-teal sky, Madhubani wave-and-fish border."
        ),
        "hz_frequency":      "174Hz",
        "title":             None,
        "thumbnail_hook":    "TOO MUCH STRESS?",
        "thumbnail_instr":   "SITAR, BANSURI & TABLA · RAAG YAMAN KALYAN",
        "thumbnail_tagline": "Drop Your Cortisol & Unwind After a Long Day",
        "playlist":          "stress",
        "suno_lyrics_style": "stress",
    },

    2: {  # Bageshri — Solo Bansuri — Anxiety / Overthinking
        "raga":        "Bageshri",
        "thaat":       "Kafi",
        "raga_mood":   "longing, introspective, late night — emotions quietly surfacing and releasing like rain",
        "instruments": ["bansuri"],
        "use_case":    "overthinking and anxiety relief",
        "theme":       "Lone bansuri in monsoon rain — the simplest sound to quiet the loudest mind",
        "music_hints": (
            "Solo bansuri, breathy and intimate. No supporting instruments for first 2.5 minutes — pure flute. "
            "Vilambit at 55 BPM. Long held komal notes that sigh and resolve, like exhaling weeks of tension. "
            "Soft tanpura drone enters at 2.5 minutes, tabla only after 4 minutes. "
            "Mood: melting, releasing, being held by the music itself."
        ),
        "image_hints": (
            "Arched Madhubani doorway with stylized monsoon rain falling outside as teardrop patterns, "
            "bansuri resting on an embroidered cushion, single candle burning beside a lotus flower, "
            "peacock sheltering under large mango leaves, deep teal and rose palette, "
            "rain drops drawn as concentric circles rippling outward in border."
        ),
        "hz_frequency":      "528Hz",
        "title":             None,
        "thumbnail_hook":    "ANXIETY WON'T GO?",
        "thumbnail_instr":   "BANSURI FLUTE SOLO · RAAG BAGESHRI",
        "thumbnail_tagline": "Stop Overthinking & Let Your Mind Finally Rest",
        "playlist":          "stress",
        "suno_lyrics_style": "stress",
    },

    3: {  # Yaman — Santoor + Tanpura — Deep Sleep
        "raga":        "Yaman",
        "thaat":       "Kalyan",
        "raga_mood":   "peaceful, uplifting, evening calm — teevra madhyam floating like a moon over still water",
        "instruments": ["santoor", "tanpura"],
        "use_case":    "deep sleep and melatonin release",
        "theme":       "Santoor crystals over tanpura drone — 432Hz releasing melatonin, body drifting into sleep",
        "music_hints": (
            "Santoor with pure crystal-hammer strokes. Vilambit at 50 BPM. "
            "Tanpura drone as unbroken low foundation. "
            "Long silences between santoor phrases — the silence is part of the music. "
            "Progressively sparser after 2 minutes. No tabla at all. "
            "Mood: drifting, weightless, each phrase further from wakefulness."
        ),
        "image_hints": (
            "Open terrace at twilight, santoor lying on silk cloth beside a glowing tanpura, "
            "crescent moon and stars drawn in Madhubani geometric spirals above, "
            "lotus pond below with fish and birds settling for the night, "
            "soft rose-violet and ivory palette, sleeping deer in corner of scene."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "CAN'T FALL ASLEEP?",
        "thumbnail_instr":   "SANTOOR & TANPURA · RAAG YAMAN",
        "thumbnail_tagline": "432Hz to Release Melatonin & Fall Asleep Fast",
        "playlist":          "sleep",
        "suno_lyrics_style": "sleep",
    },

    4: {  # Bhupali — Sitar + Sarod + Tabla — Morning Energy
        "raga":        "Bhupali",
        "thaat":       "Kalyan",
        "raga_mood":   "serene, hopeful, expansive — pentatonic openness, bright and alive at sunrise",
        "instruments": ["sitar", "sarod", "tabla"],
        "use_case":    "morning prana flow and cortisol reset",
        "theme":       "Sunrise trio — morning prana awakening, cortisol reset, body and breath in harmony",
        "music_hints": (
            "Sitar leads melody, sarod adds resonant depth below, tabla drives steady teentaal at 90 BPM. "
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
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "MORNING ANXIETY?",
        "thumbnail_instr":   "SITAR, SAROD & TABLA · RAAG BHUPALI",
        "thumbnail_tagline": "Reset Morning Cortisol & Start Your Day with Calm Energy",
        "playlist":          "morning",
        "suno_lyrics_style": "morning",
    },

    5: {  # Darbari Kanada — Sitar + Bansuri + Pakhawaj — Midnight Dhrupad
        "raga":        "Darbari Kanada",
        "thaat":       "Asavari",
        "raga_mood":   "majestic, contemplative, late-night gravity — heavy with dhrupad grandeur",
        "instruments": ["sitar", "bansuri", "pakhawaj"],
        "use_case":    "overactive mind and late night calm",
        "theme":       "Dhrupad midnight trio — pakhawaj's ancient pulse beneath sitar and bansuri, silencing the racing mind",
        "music_hints": (
            "Sitar leads with weighty alap, bansuri answers with midnight phrases after 2 minutes. "
            "Pakhawaj enters softly at 3.5 minutes with slow chautal — deeper and more ancient than tabla. "
            "40 BPM inner pulse. Deep komal rishab and komal gandhar with heavy meend. "
            "Pakhawaj barrel drum, dhrupad percussion, ancient deep drum — "
            "its resonance giving majestic dhrupad gravitas. Thoughts settling like sediment."
        ),
        "image_hints": (
            "Night court scene — sitar player, bansuri player, and pakhawaj player in a "
            "grand arched pavilion at midnight, oil lamps in a crescent arc around them, "
            "full moon drawn as mandala above, peacocks with folded wings at the edges, "
            "deep indigo, gold lamp-glow, and ivory palette, Madhubani star-field ceiling."
        ),
        "hz_frequency":      "396Hz",
        "title":             None,
        "thumbnail_hook":    "MIND WON'T STOP?",
        "thumbnail_instr":   "SITAR, BANSURI & PAKHAWAJ · RAAG DARBARI",
        "thumbnail_tagline": "Silence an Overactive Mind & Reset Your Nervous System",
        "playlist":          "midnight",
        "suno_lyrics_style": "midnight",
    },

    6: {  # Bhairavi — Bansuri + Harmonium — Morning Devotional
        "raga":        "Bhairavi",
        "thaat":       "Bhairavi",
        "raga_mood":   "devotional, melancholic, surrendered — all-komal raga of complete emotional release",
        "instruments": ["bansuri", "harmonium"],
        "use_case":    "morning cortisol reset and devotional meditation",
        "theme":       "Bansuri over harmonium warmth — Bhairavi's surrender lowering cortisol, the week's weight lifting",
        "music_hints": (
            "Bansuri warm and intimate over continuous harmonium drone. "
            "Harmonium holds Bhairavi's komal notes as a warm, sustained wave. "
            "Slow vilambit at 60 BPM. No tabla for first 3 minutes — pure bansuri and harmonium breath. "
            "Bhairavi's all-komal notes creating profound emotional depth. Mood: washing clean, surrender."
        ),
        "image_hints": (
            "Bansuri player seated at a river's edge at dawn, harmonium player beside them "
            "on a lotus-patterned mat, stylized rising sun with concentric golden rings above, "
            "lotus flowers opening on the water, birds flying in V-formation, "
            "saffron and warm gold palette, geometric fish-and-wave Madhubani border."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "CORTISOL CALM",
        "thumbnail_instr":   "BANSURI & HARMONIUM · RAAG BHAIRAVI",
        "thumbnail_tagline": "Lower Morning Cortisol & Reset for the Week Ahead",
        "playlist":          "morning",
        "suno_lyrics_style": "morning",
    },

    7: {  # Ahir Bhairav — Shehnai + Tabla + Tanpura — Morning Temple
        "raga":        "Ahir Bhairav",
        "thaat":       "Bhairav",
        "raga_mood":   "gentle awakening, hopeful yet grounded — temple at dawn, warmer than pure Bhairav",
        "instruments": ["shehnai", "tabla", "tanpura"],
        "use_case":    "morning anxiety and cortisol reset",
        "theme":       "Temple shehnai at dawn — sacred morning sound, anxiety evaporating in first light",
        "music_hints": (
            "Shehnai leading with ceremonial grace and morning purity, tanpura providing sacred drone. "
            "Tabla entering softly at 2 minutes with slow keherwa at 75 BPM. "
            "Ahir Bhairav's komal gandhar and komal dhaivat giving warmth — gentler than pure Bhairav. "
            "Shehnai reed instrument, ceremonial Indian oboe, nadaswaram style — "
            "sound of temple opening at first light. Mood: sacred calm, anxiety dissolving."
        ),
        "image_hints": (
            "Temple ghat at dawn, shehnai player seated on the steps above the river, "
            "tabla player and tanpura player beside, priest lighting diyas in background, "
            "stylized rising sun with Madhubani mandala rays, lotus flowers on the water, "
            "birds in formation across the sunrise sky, saffron and warm rose palette."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "MORNING FEEL HEAVY?",
        "thumbnail_instr":   "SHEHNAI & TABLA · RAAG AHIR BHAIRAV",
        "thumbnail_tagline": "Temple Dawn Sound to Clear Morning Anxiety",
        "playlist":          "morning",
        "suno_lyrics_style": "morning",
    },

    8: {  # Malkaunsa — Sarangi + Pakhawaj + Tanpura — Anxiety Release
        "raga":        "Malkaunsa",
        "thaat":       "Bhairavi",
        "raga_mood":   "austere, deeply meditative, midnight pentatonic — five notes carrying the weight of silence",
        "instruments": ["sarangi", "pakhawaj", "tanpura"],
        "use_case":    "anxiety and nervous system reset",
        "theme":       "Sarangi in Malkaunsa's midnight — the instrument that cries so you don't have to",
        "music_hints": (
            "Sarangi leading with raw emotional alap, each bow stroke a release of tension. "
            "Bowed sarangi, crying Indian strings, intimate bowed lute — "
            "tanpura holding the drone. Pakhawaj barrel drum, dhrupad percussion entering at 3 minutes "
            "with ancient slow rhythm at 45 BPM. Komal gandhar, nishad, dhaivat. "
            "Mood: the instrument crying so the listener doesn't have to."
        ),
        "image_hints": (
            "Midnight scene with lone sarangi player under a flowering night-jasmine tree, "
            "pakhawaj drum glowing in lamplight, tanpura lying at their feet, "
            "full moon drawn as geometric mandala above, jasmine petals falling, "
            "deep indigo and silver palette, weeping peacock motif in Madhubani border."
        ),
        "hz_frequency":      "528Hz",
        "title":             None,
        "thumbnail_hook":    "ANXIETY WON'T LEAVE?",
        "thumbnail_instr":   "SARANGI & PAKHAWAJ · RAAG MALKAUNSA",
        "thumbnail_tagline": "Let the Sarangi Carry What You Cannot — Nervous System Reset",
        "playlist":          "stress",
        "suno_lyrics_style": "stress",
    },

    9: {  # Todi — Sarod + Tabla — Deep Focus
        "raga":        "Todi",
        "thaat":       "Todi",
        "raga_mood":   "contemplative, melancholic morning — profound and searching, the scholar's raga",
        "instruments": ["sarod", "tabla"],
        "use_case":    "deep focus and intellectual clarity",
        "theme":       "Sarod in Todi's labyrinth — the raga that makes thoughts ordered and precise",
        "music_hints": (
            "Sarod exploring Todi's complex komal notes with methodical alap. "
            "Komal re, komal ga, komal dha, komal ni — each a step inward. "
            "Tabla entering at 2 minutes with sparse teentaal at 70 BPM. "
            "Sarod's resonant bass strings giving intellectual weight. "
            "Mood: the flow state, clarity without strain, deep organised thinking."
        ),
        "image_hints": (
            "Scholar's terrace at early morning, sarod player deeply absorbed in play, "
            "geometric star pattern above on arched ceiling, tabla player in focused stillness, "
            "books and lotus flowers on the mat, morning mist outside the latticed window, "
            "deep teal, ochre and ivory palette, Madhubani geometric grid border."
        ),
        "hz_frequency":      "741Hz",
        "title":             None,
        "thumbnail_hook":    "BRAIN FOG WON'T LIFT?",
        "thumbnail_instr":   "SAROD & TABLA · RAAG TODI",
        "thumbnail_tagline": "Enter the Flow State & Think With Razor Clarity",
        "playlist":          "focus",
        "suno_lyrics_style": "focus",
    },

    10: {  # Puriya Dhanashree — Santoor + Sarod + Pakhawaj — Sleep
        "raga":        "Puriya Dhanashree",
        "thaat":       "Marwa",
        "raga_mood":   "romantic, twilight, deeply emotional — longing that turns into surrender and sleep",
        "instruments": ["santoor", "sarod", "pakhawaj"],
        "use_case":    "deep sleep and emotional release before rest",
        "theme":       "Santoor and sarod at twilight — Puriya Dhanashree's bittersweet tension releasing into sleep",
        "music_hints": (
            "Santoor shimmering with twilight phrases, sarod answering from deeper registers. "
            "Pakhawaj barrel drum, ancient deep drum providing slow chautal pulse at 45 BPM after 3 minutes. "
            "Puriya Dhanashree's komal re and shuddha ni creating bittersweet twilight tension "
            "that slowly resolves. Mood: longing dissolving, body surrendering to rest."
        ),
        "image_hints": (
            "Twilight terrace above a lotus lake, santoor and sarod players facing each other, "
            "pakhawaj drum between them, lanterns glowing amber, crescent moon rising, "
            "stars drawn as Madhubani geometric spirals, deer and peacocks settling for the night, "
            "deep rose, violet and gold palette, lotus-vine Madhubani border."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "CAN'T WIND DOWN?",
        "thumbnail_instr":   "SANTOOR, SAROD & PAKHAWAJ · RAAG PURIYA DHANASHREE",
        "thumbnail_tagline": "Let Go of the Day & Fall Into Deep Peaceful Sleep",
        "playlist":          "sleep",
        "suno_lyrics_style": "sleep",
    },

    11: {  # Hamsadhwani — Bansuri + Tabla — Morning Peace
        "raga":        "Hamsadhwani",
        "thaat":       "Bilawal",
        "raga_mood":   "auspicious, clear, hopeful — pentatonic joy that doesn't force, morning welcoming",
        "instruments": ["bansuri", "tabla"],
        "use_case":    "morning focus and positive energy reset",
        "theme":       "Bansuri in Hamsadhwani — five sacred notes, infinite clarity, morning mind wide open",
        "music_hints": (
            "Bansuri with clean, bright tone exploring the auspicious pentatonic of Hamsadhwani. "
            "Teentaal at 85 BPM, tabla entering at 90 seconds — no heavy opening. "
            "No melancholy, no complexity — just opening phrases like a morning lotus. "
            "Mood: fresh, clear, auspicious beginning, cortisol dropping naturally."
        ),
        "image_hints": (
            "Garden at morning with bansuri player seated under a flowering champak tree, "
            "tabla player in sunlit corner, five lotus flowers opening one by one in the pond, "
            "stylized sunrise birds in Madhubani linework above, fresh green and gold palette, "
            "geometric honeycomb Madhubani border with bees and lotus motifs."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "CAN'T START YOUR DAY?",
        "thumbnail_instr":   "BANSURI & TABLA · RAAG HAMSADHWANI",
        "thumbnail_tagline": "Five Sacred Notes to Open Your Morning Mind",
        "playlist":          "morning",
        "suno_lyrics_style": "morning",
    },

    12: {  # Lalit — Solo Sitar — 3am / Pre-dawn
        "raga":        "Lalit",
        "thaat":       "Marwa",
        "raga_mood":   "profound, pre-dawn, deeply philosophical — the raga of the last hour before sunrise",
        "instruments": ["sitar"],
        "use_case":    "3am overactive mind and pre-dawn meditation",
        "theme":       "Sitar alone in the last hour before light — Lalit's paradox dissolving racing thoughts",
        "music_hints": (
            "Solo sitar, absolutely no rhythm support — pure alap only. "
            "Lalit's unique use of both shuddha and teevra madhyam creates tension that never fully resolves. "
            "No BPM, no pulse — just breath and the sitar. "
            "Extremely sparse — sometimes 15 seconds of silence between notes. "
            "Mood: the paradox of 3am, too tired to think, too awake to sleep, peace in that gap."
        ),
        "image_hints": (
            "Lone figure with sitar on a moonlit rooftop, pre-dawn darkness with a sliver of blue light "
            "just beginning at the horizon, a single oil lamp casting a warm circle of light, "
            "geometric crescent moon above, city silhouette below in Madhubani folk-art style, "
            "deep navy, silver moonlight and warm gold lamp-glow palette, minimal sparse border."
        ),
        "hz_frequency":      "396Hz",
        "title":             None,
        "thumbnail_hook":    "AWAKE AT 3AM?",
        "thumbnail_instr":   "SITAR SOLO · RAAG LALIT",
        "thumbnail_tagline": "The Pre-Dawn Raga to Quiet the Last Racing Thoughts",
        "playlist":          "midnight",
        "suno_lyrics_style": "midnight",
    },

    13: {  # Bhimpalasi — Bansuri + Harmonium + Tabla — Emotional Healing
        "raga":        "Bhimpalasi",
        "thaat":       "Kafi",
        "raga_mood":   "devotional, afternoon warmth, emotional surrender — the bhajan of the afternoon heart",
        "instruments": ["bansuri", "harmonium", "tabla"],
        "use_case":    "afternoon emotional healing and stress reset",
        "theme":       "Bansuri over harmonium warmth — Bhimpalasi's afternoon devotion absorbing cortisol and healing emotion",
        "music_hints": (
            "Bansuri melodic lead, harmonium providing warm sustained chord-drone below, "
            "tabla entering at 2 minutes with gentle keherwa at 80 BPM. "
            "Bhimpalasi's komal gandhar and komal nishad giving emotional depth. "
            "Harmonium devotional warmth beneath bansuri's flight. "
            "Mood: emotional release, afternoon healing, the heart softening."
        ),
        "image_hints": (
            "Afternoon courtyard with dappled sunlight, bansuri player and harmonium player "
            "on a patterned dhurrie, tabla player in shade of neem tree, "
            "marigold flowers and tulsi plant in foreground, pigeons in geometric Madhubani sky above, "
            "warm saffron, terracotta and ivory palette, floral and vine border."
        ),
        "hz_frequency":      "528Hz",
        "title":             None,
        "thumbnail_hook":    "EMOTIONALLY DRAINED?",
        "thumbnail_instr":   "BANSURI, HARMONIUM & TABLA · RAAG BHIMPALASI",
        "thumbnail_tagline": "Afternoon Devotional Music for Emotional Reset & Inner Peace",
        "playlist":          "stress",
        "suno_lyrics_style": "stress",
    },

    14: {  # Alhaiya Bilawal — Bansuri + Tabla — Morning (competitor 100K angle)
        "raga":        "Alhaiya Bilawal",
        "thaat":       "Bilawal",
        "raga_mood":   "bright, fresh, morning optimism — light touch, gently climbing phrases, spring morning",
        "instruments": ["bansuri", "tabla"],
        "use_case":    "morning anxiety relief and positive energy reset",
        "theme":       "Bansuri at spring sunrise — Alhaiya Bilawal's brightness washing morning anxiety clean",
        "music_hints": (
            "Bansuri with fresh, ascending morning phrases, clean bright tone. "
            "Teentaal at 85 BPM, tabla entering at 90 seconds. "
            "Alhaiya Bilawal's shuddha notes with occasional komal nishad for gentle depth. "
            "Competitor (SoulfulBreathscape) got 100K with this raga — replicate the morning lightness. "
            "Mood: anxiety dissolving in morning light, fresh start energy."
        ),
        "image_hints": (
            "Spring garden at sunrise, bansuri player in white kurta seated among blooming flowers, "
            "tabla player in warm morning light, stylized sunrise with ascending geometric rays, "
            "birds in formation, fresh green and saffron palette, "
            "spring flowers — jasmine and champa — woven through Madhubani border."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "MORNING ANXIETY?",
        "thumbnail_instr":   "BANSURI & TABLA · RAAG ALHAIYA BILAWAL",
        "thumbnail_tagline": "Morning Raga to Clear Anxiety & Start Fresh",
        "playlist":          "morning",
        "suno_lyrics_style": "morning",
    },

    15: {  # Madhuwanti — Sarod + Santoor — Evening Stress
        "raga":        "Madhuwanti",
        "thaat":       "Todi",
        "raga_mood":   "romantic, sweet evening, mysterious tension resolving into peace — honey at dusk",
        "instruments": ["sarod", "santoor"],
        "use_case":    "evening stress and emotional wind-down",
        "theme":       "Sarod and santoor at dusk — Madhuwanti's sweet tension releasing the week's weight",
        "music_hints": (
            "Sarod exploring Madhuwanti's unique komal gandhar and teevra madhyam combination, "
            "santoor adding crystalline responses shimmering above the sarod's depth. "
            "No tabla — pure melodic duo in slow vilambit at 55 BPM. "
            "Bittersweet evening quality, like watching the last light fade. "
            "Mood: sweet resignation, stress dissolving into acceptance and peace."
        ),
        "image_hints": (
            "Dusk terrace overlooking a river, sarod and santoor players in profile "
            "against an amber and crimson sky, peacock in full display on the parapet, "
            "first stars appearing above, oil lamps just being lit, "
            "amber, crimson and peacock-teal palette, honeyed Madhubani scroll border."
        ),
        "hz_frequency":      "174Hz",
        "title":             None,
        "thumbnail_hook":    "STRESS WON'T LEAVE?",
        "thumbnail_instr":   "SAROD & SANTOOR · RAAG MADHUWANTI",
        "thumbnail_tagline": "Rare Evening Raga to Dissolve Stress & Find Peace",
        "playlist":          "stress",
        "suno_lyrics_style": "stress",
    },

    16: {  # Vibhas — Sarangi + Tanpura — Midnight Stillness
        "raga":        "Vibhas",
        "thaat":       "Bhairav",
        "raga_mood":   "austere, pre-dawn, sparse — only five notes, creating profound emptiness and stillness",
        "instruments": ["sarangi", "tanpura"],
        "use_case":    "midnight stillness and nervous system shutdown",
        "theme":       "Sarangi in Vibhas's void — the sparsest raga, bowing silence into sound at midnight",
        "music_hints": (
            "Sarangi with immense space between each phrase — Vibhas has only 5 notes (extreme austerity). "
            "Bowed sarangi, crying Indian strings, intimate bowed lute — "
            "tanpura as the only other sound. No rhythm, pure alap. "
            "Each bow stroke separated by 8-10 seconds of silence. The silences are the music. "
            "35 BPM breath pace. Komal re and komal dha, no madhyam, no nishad. "
            "Mood: dissolving into the void, thoughts becoming nothing."
        ),
        "image_hints": (
            "Lone sarangi player in near-darkness, single lamp casting minimal light, "
            "tanpura lying horizontally in the foreground, vast empty midnight sky above "
            "with five stars drawn as Madhubani geometric points, river below completely still, "
            "deep navy and moonlit silver palette, sparse minimal Madhubani border."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "THOUGHTS WON'T STOP?",
        "thumbnail_instr":   "SARANGI & TANPURA · RAAG VIBHAS",
        "thumbnail_tagline": "The Rarest Midnight Sound — 5 Notes to Absolute Stillness",
        "playlist":          "midnight",
        "suno_lyrics_style": "midnight",
    },

    17: {  # Kedar — Sitar + Tanpura + Mridangam — Midnight Devotional
        "raga":        "Kedar",
        "thaat":       "Kalyan",
        "raga_mood":   "devotional, midnight, sacred — associated with Lord Shiva, temple at midnight",
        "instruments": ["sitar", "tanpura", "mridangam"],
        "use_case":    "late night devotional calm and inner peace",
        "theme":       "Sitar with mridangam at Shiva's midnight — North meets South in sacred rhythm",
        "music_hints": (
            "Sitar leading with devotional midnight alap, tanpura providing sacred drone. "
            "Mridangam South Indian drum, Carnatic rhythm, two-headed drum — "
            "entering at 3 minutes with slow Carnatic pulse, deeper and more resonant than tabla. "
            "Kedar's both madhyams (shuddha and teevra) creating spiritual ambiguity. "
            "50 BPM Carnatic pulse. Mood: sacred midnight energy, prayer without words."
        ),
        "image_hints": (
            "Temple sanctum at midnight, sitar player before a lit Shiva lingam, "
            "tanpura leaning against a pillar, mridangam player in ceremonial posture, "
            "oil lamps and incense smoke rising in Madhubani scroll patterns, "
            "Nandi bull in background, crescent moon on Shiva's crown motif above, "
            "deep indigo, gold lamp-glow and sacred red palette."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "NEED INNER PEACE?",
        "thumbnail_instr":   "SITAR & MRIDANGAM · RAAG KEDAR",
        "thumbnail_tagline": "Sacred Midnight Raga for Deep Inner Peace",
        "playlist":          "midnight",
        "suno_lyrics_style": "midnight",
    },

    18: {  # Pahadi — Bansuri + Sarod + Tabla — Morning Folk
        "raga":        "Pahadi",
        "thaat":       "Bilawal",
        "raga_mood":   "folk-classical, mountain morning, free and open — Pahadi means of the mountains",
        "instruments": ["bansuri", "sarod", "tabla"],
        "use_case":    "morning energy and cortisol reset with mountain-folk warmth",
        "theme":       "Mountain dawn trio — Pahadi's Himalayan freedom, cortisol melting in high-altitude air",
        "music_hints": (
            "Bansuri leading with folk-classical mountain phrases, free and open. "
            "Sarod adding Himalayan depth and resonance below. "
            "Tabla with folk-flavored keherwa at 90 BPM — lighter and more open than teentaal. "
            "Pahadi's free use of all notes creating openness unlike fixed classical ragas. "
            "Mood: mountain air, cortisol dissolving, total freedom."
        ),
        "image_hints": (
            "Mountain terrace at dawn with three musicians — bansuri, sarod, tabla — "
            "overlooking snow-capped Himalayan peaks drawn in Madhubani folk style, "
            "prayer flags fluttering above, pine trees and rhododendrons in foreground, "
            "eagle in geometric flight above, fresh blue, gold and forest-green palette, "
            "mountain-motif Madhubani border with river and peaks."
        ),
        "hz_frequency":      "432Hz",
        "title":             None,
        "thumbnail_hook":    "CAN'T WAKE UP CALM?",
        "thumbnail_instr":   "BANSURI, SAROD & TABLA · RAAG PAHADI",
        "thumbnail_tagline": "Himalayan Morning Music to Reset Cortisol & Feel Free",
        "playlist":          "morning",
        "suno_lyrics_style": "morning",
    },

    19: {  # Megh — Bansuri + Sarangi + Mridangam — Monsoon Stress Relief
        "raga":        "Megh",
        "thaat":       "Kafi",
        "raga_mood":   "monsoon joy, earthy, liberating — rain washing everything clean and ancient",
        "instruments": ["bansuri", "sarangi", "mridangam"],
        "use_case":    "monsoon stress relief and emotional release",
        "theme":       "Bansuri and sarangi in the first monsoon rain — ancient sounds for ancient relief",
        "music_hints": (
            "Bansuri with open monsoon-calling phrases that rise and fall like rain. "
            "Bowed sarangi, crying Indian strings, intimate bowed lute — adding raw earthy depth below. "
            "Mridangam South Indian drum, Carnatic rhythm, two-headed drum — "
            "monsoon pulse at 80 BPM, thunderous yet joyful. "
            "Megh's ascending phrases with monsoon liberation. "
            "Mood: the catharsis of rain, letting go completely, ancient seasonal relief."
        ),
        "image_hints": (
            "Monsoon scene with bansuri player, sarangi player and mridangam player "
            "sheltering under a large banyan tree as stylized rain falls in Madhubani teardrop patterns, "
            "peacock dancing in full display in the rain, river swelling with Madhubani wave-motifs, "
            "dark teal, stormy grey and emerald green palette with bursts of saffron, "
            "rain-and-cloud Madhubani border with dancing peacocks."
        ),
        "hz_frequency":      "528Hz",
        "title":             None,
        "thumbnail_hook":    "STRESS IN THE RAIN?",
        "thumbnail_instr":   "BANSURI, SARANGI & MRIDANGAM · RAAG MEGH",
        "thumbnail_tagline": "Monsoon Raga for Emotional Release & Stress Relief",
        "playlist":          "stress",
        "suno_lyrics_style": "stress",
    },
}

# ── Content strategy seeds (injected into Gemini brain prompt) ───────────────
CONTENT_SEEDS = {
    "outcome_hooks": [
        "Mental Clarity", "Brain Fog Gone", "Stress Detox", "Deep Focus",
        "Anxiety Reset", "Nervous System Calm", "Emotional Detox", "Mind Reset",
        "Stop Overthinking", "Morning Clarity", "Work Focus", "Inner Stillness",
        "Sleep Fast", "Wake Up Calm", "Dissolve Tension",
        # Science-backed hooks — high search intent, proven in healing music niche
        "Lower Cortisol", "Parasympathetic Reset", "Melatonin Boost", "HRV Calm",
        "Cortisol Relief", "Nervous System Reset", "Deep Nervous System Healing",
        # Competitor-validated high-view hooks (SoulfulBreathscape, ShantiofSitar)
        "Mental Health", "Sitar for Mental Health", "Calm Your Nervous System",
        "Calm Stress & Quiet Overthinking", "Calm Mind & Gentle Focus",
        "Calm, Clarity & Mental Peace", "Positive Energy & Peace",
        "Stress Relief & Deep Focus", "Relaxation & Clarity",
    ],
    "atmosphere_hooks": [
        "Monsoon Rain", "Temple at Dawn", "Candlelight", "Midnight Stillness",
        "Ganges Sunrise", "Kerala Forest", "Mountain Morning", "Rain on Leaves",
        "Desert Night", "River Fog",
    ],
    "title_patterns": [
        # ── HIGHEST PERFORMING (competitor-validated) ─────────────────────────
        # Question hook — SoulfulBreathscape gets 643K, 195K, 187K with this
        # Format: "Morning Anxiety? 🌱 | Raag X inspired Bansuri to Calm Stress"
        "{question_hook}? {emoji} | Raag {raga} inspired {instrument} to {benefit}",
        "{question_hook}? {emoji} | Raag {raga} inspired {instrument} for {use_case}",
        # Instrument-first — ShantiofSitar gets 220K, 121K with this
        # Format: "Sitar to Start Your Day | Indian Classical | Music Meditation"
        "{instrument} for {mental_health_term} | Raag {raga} | {hz} Indian Classical",
        "1 Hour {instrument} | Raag {raga} {hz} | {outcome}",
        # ── PROVEN PATTERNS (our existing) ───────────────────────────────────
        # Pain point + emoji + raga + hz + instruments + benefit
        "{pain_point} {emoji} Raag {raga} at {hz} | {instruments} for {use_case}",
        # Emotional / vulnerable hooks
        "When Your {pain_noun} Won't {verb} {emoji} Raag {raga} {hz} | {instruments} for {use_case}",
        "For the {atmosphere} {emoji} Raag {raga} at {hz} | Healing {instruments}",
        "Some Nights Your Mind Won't Slow Down {emoji} {raga} {hz} {instrument1} | Deep {outcome}",
        # Outcome-first formulas
        "{outcome} {emoji} Raag {raga} at {hz} | {instruments} for {use_case}",
        "{hz} {instruments} | {outcome} | Raag {raga}",
        # Atmosphere-led
        "{atmosphere} {emoji} {instruments} | Raag {raga} for {outcome}",
    ],
    # Question hooks that drive clicks (competitor-validated)
    "question_hooks": {
        "morning":  ["Morning Anxiety", "Can't Start Your Day", "Morning Feel Heavy",
                     "Mind Already Racing", "Cortisol Too High This Morning"],
        "stress":   ["Too Much Stress", "Anxiety Won't Go", "Mind Won't Calm Down",
                     "Can't Relax After Work", "Body Still Tense"],
        "sleep":    ["Can't Fall Asleep", "Mind Won't Stop at Night", "Sleep Won't Come",
                     "Lying Awake Again", "Overthinking at Night"],
        "focus":    ["Mind Won't Focus", "Brain Fog Won't Lift", "Stuck in Your Thoughts",
                     "Can't Concentrate", "Mind Keeps Wandering"],
        "midnight": ["Mind Won't Settle", "Overactive Mind Tonight", "Thoughts Won't Stop",
                     "Can't Quiet Your Mind", "Overthinking Before Bed"],
    },
    # Mental health terms (ShantiofSitar pattern)
    "mental_health_terms": [
        "Mental Health", "Mental Clarity", "Nervous System Calm",
        "Deep Focus", "Stress Relief", "Inner Peace", "Deep Sleep",
        "Anxiety Relief", "Emotional Healing", "Mind & Soul",
    ],
    "hook_phrases": [
        # ── Question hooks (competitor-validated — SoulfulBreathscape) ────────
        "Morning anxiety? This is your reset.",
        "Too much stress? Let this raga absorb it.",
        "Mind won't stop? Let the sitar do what sleep can't.",
        "Anxiety won't go? Ancient strings know this feeling.",
        "Stuck in your thoughts? This is the way out.",
        "Can't fall asleep? Let this raga carry you.",
        # ── Original hooks ───────────────────────────────────────────────────
        # Stress / anxiety
        "Your stress ends here.",
        "Put the world down. For now, nothing is your problem.",
        "Lower your cortisol. Slow your breath. Let this raga do the rest.",
        "Still. Ancient strings. Your nervous system finally rests.",
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
    "Authentic Madhubani (Mithila) folk-art masterpiece. "
    "Sacred, calming, spiritual, deeply connected to Indian culture and wellness traditions. "
    "Authentic Madhubani painting style, handmade folk-art appearance, museum-quality Mithila artwork. "
    "Intricate black outlines, dense decorative patterns, traditional Indian aesthetics. "
    "Every element contains authentic Madhubani decorative patterns and intricate hand-drawn textures. "
    "Exquisite Madhubani border featuring peacocks, lotus flowers, fish motifs, sacred vines, geometric Mithila patterns. "
    "Color palette: deep indigo blue, moonlit silver, earthy terracotta, warm ochre, emerald green, "
    "lotus pink, traditional Madhubani red, natural yellow pigments, subtle gold highlights. "
    "Masterpiece, ultra-detailed, 8K, professional artwork, highly intricate patterns, timeless Indian folk-art beauty. "
    "No text, no watermarks, no letters, no modern objects, no photorealism, no 3D render, no cartoon style."
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
        # Science-backed search terms from healing music niche
        "cortisol relief music", "parasympathetic music", "nervous system healing music",
    ],
    "hinglish": [
        "stress kam karne wala music", "mann shant karne ka sangeet",
        "chinta dur karne wala music", "neend ke liye music",
        "dimag shant karne wala music", "sukoon dene wala music",
    ],
}

# ── Playlists ─────────────────────────────────────────────────────────────────
# Five themed playlists — each maps to a YouTube playlist ID stored in .env.
# Create each playlist manually on YouTube Studio, then paste the ID into .env.
#
# Playlist IDs are loaded from environment variables at runtime so they never
# live in source code. Add to .env:
#   YT_PLAYLIST_MORNING=PLxxxxxxx
#   YT_PLAYLIST_FOCUS=PLxxxxxxx
#   YT_PLAYLIST_STRESS=PLxxxxxxx
#   YT_PLAYLIST_SLEEP=PLxxxxxxx
#   YT_PLAYLIST_MIDNIGHT=PLxxxxxxx
#
PLAYLISTS = {
    "morning":  {
        "name":   "Morning Raga Rituals",
        "desc":   "Start your day with intention — raga-based music to lower morning cortisol, awaken prana, and set a calm, focused tone for the day.",
        "env":    "YT_PLAYLIST_MORNING",
    },
    "focus": {
        "name":   "Focus & Brain Clarity",
        "desc":   "Indian classical music to dissolve brain fog, sharpen concentration, and lock into deep work. Ancient frequencies meet modern productivity.",
        "env":    "YT_PLAYLIST_FOCUS",
    },
    "stress": {
        "name":   "Stress & Overthinking Relief",
        "desc":   "Raga therapy for the overworked mind — drop cortisol, quiet overthinking, and let the nervous system breathe after a long day.",
        "env":    "YT_PLAYLIST_STRESS",
    },
    "sleep": {
        "name":   "Sleep & Deep Rest",
        "desc":   "432Hz raga sessions designed to release melatonin, slow the breath, and guide you into deep, uninterrupted sleep.",
        "env":    "YT_PLAYLIST_SLEEP",
    },
    "midnight": {
        "name":   "Midnight Calm",
        "desc":   "For the nights your mind won't stop — late-night raga to silence an overactive mind, reset the nervous system, and find stillness.",
        "env":    "YT_PLAYLIST_MIDNIGHT",
    },
    "shorts": {
        "name":   "Shorts",
        "desc":   "30-60 second previews of DhunDetox Indian classical music.",
        "env":    "YT_PLAYLIST_SHORTS",
    },
}


def get_playlist_id(key: str) -> str:
    """Return the YouTube playlist ID for a given key, or '' if not set."""
    entry = PLAYLISTS.get(key)
    if not entry:
        return ""
    return os.environ.get(entry["env"], "")


# ── Video format ──────────────────────────────────────────────────────────────
VEO_CLIP_SEC = 8

# ── FFmpeg ────────────────────────────────────────────────────────────────────
# Shotcut ships ffmpeg.exe but not ffprobe. We add its dir to PATH so all
# subprocess calls to "ffmpeg" resolve without full paths.
FFMPEG_DIR = r"C:\Program Files\Shotcut"
if os.name == "nt" and os.path.exists(FFMPEG_DIR) and FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# ── Output paths ──────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def today_schedule() -> dict:
    """Return today's schedule entry from the 20-day CONTENT_CALENDAR (cycles via day-of-year % 20)."""
    return CONTENT_CALENDAR[date.today().toordinal() % 20]


def format_instruments(instruments: list) -> str:
    """'sitar' | 'sitar & bansuri' | 'sitar, sarod & tabla'"""
    if len(instruments) == 1:
        return instruments[0]
    if len(instruments) == 2:
        return f"{instruments[0]} & {instruments[1]}"
    return f"{', '.join(instruments[:-1])} & {instruments[-1]}"
