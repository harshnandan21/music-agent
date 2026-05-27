"""
Step 1 — Brain
Reads today's WEEKLY_SCHEDULE from config (single source of truth).
Fields set in the schedule are locked — passed to Gemini as hard constraints
and then force-merged into the output so they cannot drift.
Gemini only writes: title (if not locked), description, tags, music_prompt,
image_prompt, video_prompt, hook_angle.
"""

import json, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    BRAIN_MODEL, OUTPUT_DIR,
    today_schedule, format_instruments,
    CONTENT_SEEDS, MADHUBANI_STYLE,
    VIDEO_ANIMATION_GUIDE, YOUTUBE_KEYWORDS,
)

USED_IDEAS_FILE = os.path.join(os.path.dirname(OUTPUT_DIR), "used_ideas.json")


def _load_used_ideas(n: int = 20) -> list:
    if not os.path.exists(USED_IDEAS_FILE):
        return []
    with open(USED_IDEAS_FILE) as f:
        data = json.load(f)
    return data[-n:]


def _save_used_idea(brain: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = []
    if os.path.exists(USED_IDEAS_FILE):
        with open(USED_IDEAS_FILE) as f:
            data = json.load(f)
    today = str(date.today())
    entry = {
        "date":              today,
        "title":             brain.get("title", ""),
        "description":       brain.get("description", ""),
        "keywords":          brain.get("keywords", ""),
        "tags":              brain.get("tags", []),
        "raga":              brain.get("raga", ""),
        "instrument":        brain.get("instrument", ""),
        "use_case":          brain.get("use_case", ""),
        "hook_angle":        brain.get("hook_angle", ""),
        "hook_phrase":       brain.get("hook_phrase", ""),
        "music_prompt":      brain.get("music_prompt", ""),
        "image_prompt":      brain.get("image_prompt", ""),
        "thumbnail_hook":    brain.get("thumbnail_hook", ""),
        "thumbnail_tagline": brain.get("thumbnail_tagline", ""),
    }
    # Replace today's entry if one already exists, otherwise append
    if data and data[-1]["date"] == today:
        data[-1] = entry
    else:
        data.append(entry)
    with open(USED_IDEAS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def run(client) -> dict:
    schedule       = today_schedule()
    instruments_label = format_instruments(schedule["instruments"])
    used           = _load_used_ideas()
    used_summary   = (
        "\n".join(f"- {e['title']}  [{e['date']}]" for e in used)
        or "None yet — this is the first video."
    )

    # ── Collect locked override values from config ────────────────────────────
    # Any key set (non-None) in the schedule is a hard constraint.
    locked = {}
    for key in ("hz_frequency", "title", "thumbnail_hook", "thumbnail_instr", "thumbnail_tagline", "hook_phrase", "playlist"):
        val = schedule.get(key)
        if val:
            locked[key] = val

    # Build the locked-values section for the Gemini prompt
    if locked:
        locked_lines = "\n".join(f'  "{k}": "{v}"' for k, v in locked.items())
        locked_section = (
            "\nLOCKED VALUES — copy these exactly into the JSON output, do not change them:\n"
            + locked_lines
        )
    else:
        locked_section = ""

    # Title instruction
    if "title" in locked:
        title_instruction = f'Use exactly this title: "{locked["title"]}"'
    else:
        title_instruction = (
            "Write the best SEO title (≤70 chars): name the raga + instruments, "
            "address a real pain point, include hz_frequency if provided."
        )

    seeds_outcomes  = ", ".join(CONTENT_SEEDS["outcome_hooks"][:14])
    seeds_atmos     = ", ".join(CONTENT_SEEDS["atmosphere_hooks"][:8])
    seeds_patterns  = "\n".join(f"  · {p}" for p in CONTENT_SEEDS["title_patterns"])
    seeds_hooks     = "\n".join(f"  · {p}" for p in CONTENT_SEEDS["hook_phrases"][:8])
    seeds_avoid     = ", ".join(CONTENT_SEEDS["avoid_generic"])
    hz_note         = f"Hz frequency for this post: {locked['hz_frequency']}" if "hz_frequency" in locked else ""

    hashtag_str = (
        " ".join(CONTENT_SEEDS["hashtag_tiers"]["big"]) + " "
        + " ".join(CONTENT_SEEDS["hashtag_tiers"]["medium"]) + " "
        + " ".join(CONTENT_SEEDS["hashtag_tiers"]["niche"]) + " "
        + " ".join(CONTENT_SEEDS["hashtag_tiers"]["hindi"])
    )
    eng_keywords = ", ".join(YOUTUBE_KEYWORDS["english"][:12])
    hinglish_keywords = ", ".join(YOUTUBE_KEYWORDS["hinglish"][:6])

    prompt = f"""You are the creative strategist for DhunDetox — a YouTube channel using Indian classical music for mental wellness.

CHANNEL: DhunDetox helps urban professionals (25-40yo, India + global diaspora) with stress, focus, sleep, anxiety through sitar, bansuri, tabla, tanpura, santoor, sarod, veena. Brand: calm, grounded, healing through sound.

TODAY'S POST CONFIG (from weekly schedule):
- Raga:        {schedule['raga']} — {schedule['raga_mood']}
- Instruments: {instruments_label}
- Use case:    {schedule['use_case']}
- Theme:       {schedule['theme']}
{hz_note}

CONTENT SEEDS (weave 1-2 naturally):
- Outcome hooks: {seeds_outcomes}
- Atmosphere hooks: {seeds_atmos}
- Title patterns (emotional/vulnerable hook preferred — highest CTR for this niche):
{seeds_patterns}
- Real examples of winning titles:
  · "Late Night Anxiety Relief 🌙 Raag Darbari Kanada at 396Hz | Sitar, Bansuri & Tabla for Overthinking"
  · "When Your Mind Won't Sleep 🌙 Raag Darbari Kanada 396Hz | Sitar for Anxiety & Overthinking"
  · "For the Sleepless Nights 🌙 Raag Darbari Kanada at 396Hz | Healing Sitar, Bansuri & Tabla"
  · "Some Nights Your Mind Won't Slow Down 🌙 Darbari Kanada 396Hz Sitar | Deep Anxiety Relief"
  Rule: pain point or relatable moment first → emoji → Raag name + Hz → instruments → benefit
- Emotional hook openers for description (pick the most fitting):
{seeds_hooks}

AVOID in title/description: {seeds_avoid}

RECENTLY PUBLISHED (do NOT repeat these angles):
{used_summary}
{locked_section}

TASK: {title_instruction}
Return pure JSON only — no markdown, no extra text.

MUSIC PROMPT GUIDANCE (for Lyria — think like Indian classical recording engineer):
- State instruments, raga, BPM (35-55 for meditation, 40-45 most soothing)
- Include: each note decays with long reverb, wide silence between phrases, no buildup no climax
- Include: warm analog recording quality, loop-friendly structure, deeply meditative
- Specify playing feel: meend glides, komal notes, alap style, how tabla enters
- Anti-patterns to explicitly exclude: no Western instruments, no percussion fills, no sudden dynamics
- Base on: {schedule['music_hints']}

IMAGE PROMPT GUIDANCE (choose Madhubani folk art — standard for this channel):
- Madhubani style: {MADHUBANI_STYLE}
- Scene base: {schedule['image_hints']}
- Always end with: "No text or letters anywhere. Pure illustration only. No watermarks."

THUMBNAIL PROMPT GUIDANCE (16:9 YouTube thumbnail — rich painterly style):
Generate thumbnail_prompt using this EXACT visual formula. This is a SEPARATE image from the background — it must include baked-in text and a storytelling visual split.

STYLE: Rich Indian folk-art painting — Mughal miniature meets Madhubani. Intricate hand-painted textures, warm earthy pigments, decorative botanical borders. NOT flat/digital. Painterly, detailed, illustrative.

STRUCTURE:
- Centre: {instruments_label} player seated cross-legged, eyes gently closed, peaceful expression, ornate saree/outfit matching the raga's mood colour
- Left half: the PROBLEM visual — derive from use_case (e.g. overthinking = tangled spirals, stress = tension lines, insomnia = restless waves, brain fog = dark clouds, anxiety = frantic hatching lines) — these dissolve/unravel as they meet the music
- Right half: the RELIEF visual — the raga's signature nature element (peacock for Bageshri/Darbari, deer for Yaman, lotus bloom for Bhairavi, crescent moon for Chandrakauns, sunrise birds for Bhupali, river heron for any water scene)
- Music: swirling notes and smoke-like wisps flow from instrument outward toward both sides
- Background: sky matching raga time-of-day — left stormy/tense transitioning to warm golden glow behind musician
- Botanicals: large lotus flowers bottom corners, mango/banyan tree branches arching overhead, small birds perching on branches
- Border: intricate paisley and lotus motif border on all four edges

TEXT OVERLAY (baked into image):
Top of image: wide ornate parchment banner with floral border containing:
  Line 1 (large bold serif): the thumbnail title — derive a SHORT punchy version of the title (max 6-7 words, no emojis, no Hz)
  Line 2 (smaller elegant serif): "Raag {schedule['raga']} · {{hz_frequency}} | {{use_case benefit, 2-3 words}}"

COLOUR PALETTE: derive from raga mood — e.g. monsoon=deep indigo+teal+rose, midnight=dark navy+gold, dawn=saffron+rose+ivory, dusk=amber+teal+crimson. Always warm golden glow behind the central musician.

OUTPUT: write thumbnail_prompt as one cohesive detailed paragraph that a text-to-image model can follow directly. Do NOT use bullet points in the output — write it as flowing descriptive text.

VIDEO PROMPT GUIDANCE (for Veo — seamless 8-second loop):
Generate video_prompt in this EXACT format, derived from the image scene above:

"Animate this image as a seamless loop video.
Camera completely static and locked, no movement.

Only animate these subtle elements:
- [pick 3-5 natural elements FROM the image scene: flames, water, sky glow, mist, clouds, birds, leaves, smoke — with action and percentage]

Everything else completely frozen and still:
[list ALL musicians, instruments, animals, plants, decorative elements from the image scene].

First frame and last frame must be identical.
No brightness change. No color shift. No flicker.
8 second seamless loop.
Madhubani folk art style preserved exactly.
[one-line mood/atmosphere sentence matching the image scene]."

Rules:
- Musicians and instruments ALWAYS frozen (never animate)
- Animals (peacocks, deer, fish) ALWAYS frozen
- Flames: 5%, water ripples: 3-5%, sky glow: 2%, leaves: 3%, smoke: 80%, birds/clouds: drifting slowly (no %)
- List every frozen element explicitly so nothing gets accidentally animated

DESCRIPTION TEMPLATE — follow this structure exactly:

{{emoji matching use case}} {{SEO title repeat}}

{{2-3 sentence hook: address the pain point directly, short and punchy}}

This deeply meditative composition in Raag {schedule['raga']} blends the healing resonance of {{hz_frequency}} — known for {{hz benefit}} — with soulful {instruments_label} to {{use case benefits}}.

"{{hook_phrase}}"

{{2-3 sentences: cultural/historical context of Raag {schedule['raga']}, what it does to the nervous system}}

{{emoji}} PERFECT FOR:
- {{8 specific use cases as bullet points}}

🎵 WHY RAAG {schedule['raga'].upper()} HEALS:
{{2-3 sentences: parasympathetic nervous system, raga science, Hz frequency benefit if applicable}}

🎧 HOW TO USE THIS MUSIC:
1. Use headphones at a comfortable, low volume
2. Dim the lights or turn them off completely
3. Lie down or sit comfortably with eyes closed
4. Take 3 slow deep breaths — exhale longer than you inhale
5. Let the {{primary instrument}} guide your thoughts into softness
6. Let the {{secondary instrument}} slow your breath
7. Let the {{third instrument or rhythm}} ground you in peace
8. Stay for at least 15–20 minutes for the full effect

────────────────────────────

🇮🇳 हिंदी में:
{{3-4 lines in Hindi describing raga, instruments, use case}}
"{{hook_phrase translated to Hindi}}"

────────────────────────────

💛 If this music brought you stillness tonight, please LIKE, SUBSCRIBE, and SHARE with someone who needs peace.
🔔 Subscribe to DhunDetox for more healing frequencies, Indian classical meditation music, raga therapy, and mindful sound journeys.
💬 Comment below: {{engaging question related to this video's theme}}
🌿 Save this video for when you need it most.

────────────────────────────

⚠️ Disclaimer: This music is intended for relaxation, meditation, and wellness purposes. It is not a substitute for professional medical or psychological treatment.

{hashtag_str}

KEYWORD STRING (separate field — for YouTube tags):
Comma-separated, no spaces after commas, total 470–480 chars exactly.
Pattern: raga name variations → instrument + raga combos → instrument alone → meditation/healing/use-case terms → emotion terms → channel name (thelifemerit) → 2-3 Hindi keywords at end (e.g. ध्यान संगीत,<instrument> संगीत,राग <raga in Devanagari>).
Do NOT include Hz frequency terms in the keyword string.
Example: raag {schedule['raga'].lower()},raga {schedule['raga'].lower()},{instruments_label.replace(' & ', ' ').replace(', ', ' ')},indian classical music,meditation music,healing music,...,thelifemerit,ध्यान संगीत,राग {schedule['raga'].lower()}

TAGS GUIDANCE: Exactly 15 tags max — English only, each max 30 chars, total under 400 chars combined. Parse from the English keywords above (exclude Hindi).

{{
  "title": "best of the 3 title_options below — pick the strongest SEO + CTR option",
  "title_options": [
    "option 1 — emotional/vulnerable hook: When... / For the... / Some nights... formula",
    "option 2 — outcome-first: raga + hz + instruments + benefit, lead with the result",
    "option 3 — atmosphere-led: scene or mood first, then raga + instruments"
  ],
  "description": "Full YouTube description following the 11-section template above, including Hindi section, CTA, disclaimer, and 15 hashtags at end",
  "keywords": "comma-separated keyword string, 470-480 chars, no spaces after commas, for YouTube tags field",
  "tags": ["15 tags parsed from keywords, English only, each max 30 chars"],
  "music_prompt": "Detailed Lyria prompt per music guidance above",
  "image_prompt": "Madhubani painting scene per image guidance above",
  "video_prompt": "Veo 8-second seamless loop per video guidance above",
  "raga": "{schedule['raga']}",
  "instrument": "{instruments_label}",
  "use_case": "{schedule['use_case']}",
  "visual_style": "madhubani_folk",
  "hook_angle": "one short phrase — unique emotional angle of this video (anti-repeat tracking)",
  "hook_phrase": "the 2-sentence emotional opener used at start of description — standalone, punchy",
  "thumbnail_hook": "2-4 ALL-CAPS word hook for thumbnail",
  "thumbnail_instr": "Instruments & Raga line for thumbnail middle",
  "thumbnail_tagline": "6-10 word benefit tagline for thumbnail bottom",
  "thumbnail_prompt": "Full Gemini image prompt for the YouTube thumbnail per thumbnail guidance above — flowing paragraph, includes text overlay instructions, visual split storytelling, colour palette, style notes"
}}"""

    response = client.models.generate_content(model=BRAIN_MODEL, contents=prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text.strip())

    # Force-merge schedule overrides — config always wins over Gemini
    data.update(locked)

    _save_used_idea(data)
    def _p(s): print(str(s).encode("ascii", "replace").decode("ascii"))
    _p(f"[brain] Raga={data['raga']} | Instruments={data['instrument']} | Hz={locked.get('hz_frequency', 'none')}")
    _p(f"[brain] Title: {data['title']}")
    for i, t in enumerate(data.get("title_options", []), 1):
        _p(f"[brain] Title option {i}: {t}")
    _p(f"[brain] Hook: {data.get('thumbnail_hook')} | Tagline: {data.get('thumbnail_tagline')}")

    kw_len = len(data.get("keywords", ""))
    if not (470 <= kw_len <= 480):
        print(f"[brain] WARNING: keyword string is {kw_len} chars (target 470-480)")

    return data


if __name__ == "__main__":
    import pprint
    from google import genai as _genai
    _client = _genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    pprint.pprint(run(_client))
