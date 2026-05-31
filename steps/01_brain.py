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

IMAGE PROMPT GUIDANCE (16:9 video background — rich Indian painterly style):
Style: Rich Indian painting — Mughal miniature meets regional folk art (Madhubani, Pahari, Pattachitra).
NOT flat/digital. Painterly, textured, deeply detailed, illustrative. Warm earthy pigments on aged parchment.
Intricate hand-painted feel with fine crosshatching and stippling. Ornate botanical borders on all edges.

Scene base to work from: {schedule['image_hints']}

COMPOSITION — invent a fresh, polished approach that fits the raga and use case. Some archetypes:
- Immersive landscape: musician(s) fully embedded in a rich atmospheric setting — river at dawn, monsoon garden,
  moonlit terrace, forest clearing — with visible sound/music flowing outward as wisps, ripples, or light
- The living scene: musician at centre surrounded by the raga's nature world — peacocks, deer, lotus,
  birds — all gathered as if drawn by the music, rich foliage framing
- The contemplative portrait: musician large in frame, instrument prominent, atmospheric landscape
  behind them — painterly like a classical Indian miniature painting, mood-heavy
- The two-world: one half of the scene shows tension/stillness (dark sky, bare branches, still water),
  the other half shows bloom/relief (golden light, flowers opening, birds in flight) — musician at threshold
- Or invent a composition entirely fitting to the specific raga, instruments, and emotion

Key rules:
- Central figure: the {instruments_label} player(s), eyes closed or deeply focused, serene
- Music flows visibly — as wisps, smoke, notes, light rays, ripples — from the instrument into the scene
- Raga's signature nature elements must be present (peacock=Bageshri/Darbari, deer=Yaman, lotus=Bhairavi,
  crescent moon=Chandrakauns, sunrise birds=Bhupali, river heron=water scenes)
- Colour palette derived from raga mood and time of day:
    monsoon/night → deep indigo, stormy teal, rose, silver
    dawn → saffron, warm gold, ivory, fresh green
    dusk → amber, crimson, peacock teal, turmeric
    midnight → dark navy, deep violet, gold lamp-glow
- Warm golden glow or soft halo behind the central musician
- No text, no watermarks, no letters anywhere. Pure illustration only.

THUMBNAIL PROMPT GUIDANCE (16:9 YouTube thumbnail — rich painterly style):
Generate thumbnail_prompt as a SEPARATE image from the background. This is the YouTube thumbnail — it must have baked-in text and strong visual storytelling. Be creative with the composition — do NOT repeat the same layout every time.

STYLE PRINCIPLES (always apply):
- Rich Indian painting — Mughal miniature meets folk art. NOT flat or digital. Painterly, textured, illustrative, intricate.
- Central figure: the {instruments_label} player — seated, eyes closed, serene, ornate outfit in colours matching the raga's mood
- Music flows visibly from the instrument — as wisps, smoke, notes, ripples, light — connecting to the world around them
- The scene tells the emotional story of the raga and use case through symbolism, not text
- Ornate decorative border on all four edges — paisley, lotus, geometric motifs
- Rich botanical elements natural to the scene — derive from raga setting

TEXT OVERLAY (always include, baked into image):
A wide ornate parchment or stone banner (top or woven naturally into the composition) containing:
  Line 1 (large bold serif, high contrast): short punchy version of title — max 6 words, no emojis, no Hz numbers
  Line 2 (smaller elegant serif): "Raag {schedule['raga']} · {{hz_frequency}}  |  {{2-3 word benefit}}"

COMPOSITION — invent a fresh approach each time. Some possibilities to draw from:
- The two-world split: musician at centre, one half shows the emotional problem (tangled spirals for overthinking, dark storm clouds for stress, fragmented shards for anxiety, grey fog for brain fatigue), other half shows the relief (peacock in full bloom, deer in golden light, lotus opening, moon emerging from clouds) — both halves dissolving into the music
- The immersive scene: musician fully embedded in a rich landscape — river at dawn, monsoon garden, moonlit terrace — the music animates the whole scene with visible sound waves
- The before/after arch: upper half dark and chaotic, lower half calm and luminous, musician at the threshold playing the transition
- The circular mandala: musician at centre of a radiant circular composition, raga's nature symbols radiating outward like petals, problem symbols at outer edges dissolving inward
- The atmospheric portrait: musician large in frame, face and instrument dominant, atmospheric landscape behind — painterly like a classical Indian portrait but with visible sound and emotion
- Or invent something entirely fitting to the specific raga and use case

COLOUR PALETTE: always derive from raga mood and time of day
  monsoon/night ragas → deep indigo, stormy teal, rose, silver rain
  dawn ragas → saffron, warm gold, ivory, fresh green
  dusk ragas → amber, crimson, peacock teal, turmeric
  midnight ragas → dark navy, deep violet, gold lamp-glow
  Always: warm golden halo or glow behind the central musician

OUTPUT: write thumbnail_prompt as one flowing paragraph of rich descriptive prose — as if briefing a master illustrator. Do NOT use bullet points. Make it specific, vivid, and unique to this raga and use case.

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

DESCRIPTION TEMPLATE — follow this structure exactly. Target: 300–400 words total.

SECTION 1 — First 125 characters (CRITICAL — shown before "Show more" button. Keywords first, NO emoji at start):
Write as: "Raag {{raga}} {{hz_frequency}} for {{primary benefit}}. {{instruments}} {{use case}} meditation music."
Example: "Raag Bhairavi 432Hz for morning cortisol reset. Bansuri & Tanpura deep meditation music for stress relief."

SECTION 2 — Hook (2–3 sentences, punchy, addresses the pain point):
{{emotional hook}}

"{{hook_phrase}}"

SECTION 3 — CHAPTERS (REQUIRED — paste exactly, YouTube indexes each line as a keyword):
0:00 Introduction — Setting the Intention
5:00 Alap — Free Exploration of Raag {schedule['raga']}
15:00 Vilambit — Slow & Deep Meditation
35:00 Madhya Laya — Deepening the Stillness
52:00 Samapti — Resolution & Inner Peace
58:00 Outro — Carry the Calm Forward

SECTION 4 — Raga context (2–3 sentences max):
{{Cultural/historical context of Raag {schedule['raga']}, what it does to the nervous system, Hz benefit}}

SECTION 5 — PERFECT FOR (6 bullets, specific):
{{emoji}} PERFECT FOR:
- {{6 specific use cases}}

SECTION 6 — WHY IT HEALS (2 sentences, concise):
🎵 WHY RAAG {schedule['raga'].upper()} HEALS:
{{2 sentences — parasympathetic nervous system, raga science}}

────────────────────────────

🇮🇳 हिंदी में:
{{3–4 lines in Hindi describing raga, instruments, use case}}
"{{hook_phrase in Hindi}}"

────────────────────────────

💛 If this music brought you stillness, please LIKE, SUBSCRIBE, and SHARE with someone who needs peace.
🔔 Subscribe to DhunDetox for daily Indian classical healing music, raga therapy, and mindful sound journeys.
💬 Comment below: {{one engaging question for this video's theme}}
🌿 Save this video for when you need it most.

────────────────────────────

⚠️ Disclaimer: This music is intended for relaxation and wellness. Not a substitute for professional medical treatment.

{hashtag_str}

KEYWORD STRING (separate field — for YouTube tags):
Comma-separated, no spaces after commas, total 470–480 chars exactly.
Pattern: raga name variations → instrument + raga combos → instrument alone → meditation/healing/use-case terms → emotion terms → channel name (thelifemerit) → 2-3 Hindi keywords at end (e.g. ध्यान संगीत,<instrument> संगीत,राग <raga in Devanagari>).
Do NOT include Hz frequency terms in the keyword string.
Example: raag {schedule['raga'].lower()},raga {schedule['raga'].lower()},{instruments_label.replace(' & ', ' ').replace(', ', ' ')},indian classical music,meditation music,healing music,...,thelifemerit,ध्यान संगीत,राग {schedule['raga'].lower()}

TAGS GUIDANCE: Target 440–460 chars (YouTube shows 500 but rejects above ~465 in practice). English only. First tag = primary keyword (raag name). Then: raga name variations, instrument+raga combos, instrument alone, broad categories (meditation music, healing music, stress relief), long-tail benefit combos (raag X for anxiety, X meditation), emotion/use-case terms, channel brand (dhundetox) last. Each tag with spaces counts +2 chars toward the budget. Aim for 22–26 quality tags.

{{
  "title": "best of the 3 title_options below — pick the strongest SEO + CTR option",
  "title_options": [
    "option 1 — emotional/vulnerable hook: When... / For the... / Some nights... formula",
    "option 2 — outcome-first: raga + hz + instruments + benefit, lead with the result",
    "option 3 — atmosphere-led: scene or mood first, then raga + instruments"
  ],
  "description": "Full YouTube description following the template above (300–400 words). First 125 chars must be keyword-first. Chapters at section 3. Hindi section, CTA, disclaimer, hashtags at end.",
  "keywords": "comma-separated keyword string, 470-480 chars, no spaces after commas, for YouTube tags field",
  "tags": ["8 tags — primary keyword first, then broad, then long-tail, then dhundetox"],
  "chapters": [
    {{"time": "0:00", "title": "Introduction — Setting the Intention"}},
    {{"time": "5:00", "title": "Alap — Free Exploration of Raag {{raga}}"}},
    {{"time": "15:00", "title": "Vilambit — Slow & Deep Meditation"}},
    {{"time": "35:00", "title": "Madhya Laya — Deepening the Stillness"}},
    {{"time": "52:00", "title": "Samapti — Resolution & Inner Peace"}},
    {{"time": "58:00", "title": "Outro — Carry the Calm Forward"}}
  ],
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
  "thumbnail_tagline": "6-10 word benefit tagline for thumbnail bottom"
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
