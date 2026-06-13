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
    CONTENT_SEEDS, IMAGE_STYLE_V2,
    VIDEO_ANIMATION_GUIDE, YOUTUBE_KEYWORDS,
)

USED_IDEAS_FILE = os.path.join(os.path.dirname(OUTPUT_DIR), "used_ideas.json")

# Cinematic mood backdrops keyed by playlist type.
# These are the base scene descriptions for the Madhubani Hybrid image system:
# cinematic Indian scene in the centre, Madhubani ornamental border on all edges.
# Source: thumbnail design brief analysis — differentiates from every competitor
# who uses generic photographic landscapes with no folk-art identity.
_MOOD_BACKDROP = {
    "morning": (
        "Cinematic Indian sunrise landscape, soft golden mist over a serene river, "
        "distant Himalayan silhouette, warm peach-saffron-gold sky at the horizon, "
        "deep indigo-rose at the top fading to warm amber at sunrise"
    ),
    "sleep": (
        "Cinematic moonlit Indian night scene, full moon over the Yamuna river, "
        "distant temple silhouette with glowing oil lamps, deep indigo and purple night sky "
        "with subtle stars, soft golden lamp reflections shimmering in still water"
    ),
    "midnight": (
        "Cinematic Indian midnight scene, crescent moon above an ancient temple, "
        "oil lamps glowing warm gold in the foreground, deep navy and indigo sky, "
        "river below perfectly still, subtle star-field in soft geometric patterns"
    ),
    "stress": (
        "Cinematic Indian monsoon scene, gentle rain falling over lush green Kerala backwaters, "
        "ancient temple in the distance, mist rising from rain-soaked earth, "
        "deep teal and forest green palette with warm gold highlights"
    ),
    "focus": (
        "Cinematic serene Indian forest meditation grove, ancient banyan tree with soft dappled "
        "morning sunlight, deep sage green and forest tones, warm gold light shafts through the "
        "canopy, peaceful clearing with wildflowers and moss-covered ground"
    ),
}


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
    for key in ("hz_frequency", "title", "thumbnail_hook", "thumbnail_instr", "thumbnail_tagline",
                "hook_phrase", "playlist", "thaat", "suno_lyrics_style"):
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
            "Generate 8 SEO-optimised title options (≤70 chars each). "
            "Pick the strongest as 'title'. Put all 8 in 'title_options'.\n\n"
            "SEO TITLE PATTERNS — use ALL 8, one per pattern:\n\n"
            "  ★★ #1 FORMULA — Neuroscience + Raga (Raga Heal: 384K + 368K views, highest in niche):\n"
            "  Pattern N — '[Wellness/Science Term] [Emoji] | [Raga] [Instrument] [Hz] for [Benefit1], [Benefit2] & [Benefit3]'\n"
            "    Wellness terms: Dopamine Reset · Cortisol Drop · Vagus Nerve · Digital Detox\n"
            "                    Nervous System Reset · Circadian Reset · Screen Fatigue · Burnout Reset\n"
            "    Examples: 'Dopamine Reset 🌿 | Bansuri Raga Bhimpalasi 432Hz for Focus, Calm & Inner Peace'\n"
            "              'Vagus Nerve Reset | Veena Raga Bhairavi 432Hz for Deep Calm & Anxiety Relief'\n"
            "              'Digital Detox | Santoor Raga Yaman 432Hz for Screen Fatigue, Sleep & Mental Clarity'\n"
            "              'Cortisol Drop 🌿 | Sitar Raga Bhupali 432Hz for Morning Calm, Focus & Anxiety Relief'\n\n"
            "  ★ HIGHEST PERFORMING (competitor-validated view counts):\n"
            "  Pattern A — Question hook (643K views): '{Question}? 🌱 | Raag X inspired {Instrument} to {benefit}'\n"
            "    Examples: 'Morning Anxiety? 🌱 | Raag Bhairavi inspired Bansuri to Calm Stress'\n"
            "              'Too Much Stress? 🌱 | Raag Chandrakauns inspired Sitar for Clarity'\n"
            "              'Anxiety Wont Go? 🌱 | Raag Yaman inspired Sitar & Bansuri for Peace'\n"
            "    → Use the question hooks provided in CONTENT SEEDS for today's use case\n\n"
            "  Pattern B — Instrument-first (220K views): '{Instrument} for {Mental Health Term} | Raag X | {Hz}'\n"
            "    Examples: 'Sitar for Mental Health | Raag Yaman Kalyan | 174Hz Indian Classical'\n"
            "              'Bansuri for Stress Relief | Raag Bhairavi | 432Hz Meditation'\n\n"
            "  Pattern C — 1 Hour explicit (121K views): '1 Hour {Instrument} | Raag X {Hz} | {Outcome}'\n"
            "    Examples: '1 Hour Sitar | Raag Darbari 396Hz | Deep Midnight Calm'\n"
            "              '1 Hour Bansuri | Raag Bhairavi 432Hz | Morning Cortisol Reset'\n\n"
            "  ★ PROVEN PATTERNS (our channel):\n"
            "  Pattern D — Benefit-first:   'Melt Evening Stress | Raag X | Sitar & Bansuri 174Hz'\n"
            "  Pattern E — Hz-first:        '174Hz Cortisol Drop | Raag X | Sitar & Bansuri Evening'\n"
            "  Pattern F — Intent-first:    'Unwind After Work | Yaman Kalyan Sitar & Bansuri | 174Hz'\n"
            "  Pattern G — Emotional hook:  'Release the Day 🌆 Raag X 174Hz | Sitar & Bansuri'\n"
            "  Pattern H — Compressed hook: 'Stress Melt 🌆 Raag X 174Hz | Sitar & Bansuri Evening'\n\n"
            "RULES:\n"
            "  · Patterns A, B, C MUST be included — they have the highest proven view counts\n"
            "  · Each title must include: raga name + Hz + instruments + use-case benefit\n"
            "  · Pattern A: use 'Raag X inspired' phrasing (broader audience appeal)\n"
            "  · Pattern A: use question hooks from CONTENT SEEDS matching today's use case\n"
            "  · Use pipe | to separate clauses\n"
            "  · Max 1 emoji per title\n"
            "  · All ≤70 chars\n"
        )

    seeds_outcomes  = ", ".join(CONTENT_SEEDS["outcome_hooks"][:18])
    seeds_atmos     = ", ".join(CONTENT_SEEDS["atmosphere_hooks"][:8])
    seeds_patterns  = "\n".join(f"  · {p}" for p in CONTENT_SEEDS["title_patterns"])
    seeds_hooks     = "\n".join(f"  · {p}" for p in CONTENT_SEEDS["hook_phrases"][:12])
    # Question hooks — drive from playlist key (morning/sleep/focus/midnight/stress)
    q_key         = schedule.get("playlist", "stress")
    q_hooks       = ", ".join(CONTENT_SEEDS.get("question_hooks", {}).get(q_key, []))
    mh_terms      = ", ".join(CONTENT_SEEDS.get("mental_health_terms", [])[:8])
    neuro_hooks   = ", ".join(CONTENT_SEEDS.get("neuroscience_hooks", []))
    mood_backdrop = _MOOD_BACKDROP.get(q_key, _MOOD_BACKDROP["stress"])
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
- Neuroscience/wellness hooks (Raga Heal formula — 384K + 368K views): {neuro_hooks}
- Mental health terms (ShantiofSitar pattern): {mh_terms}
- Question hooks for today's use case (SoulfulBreathscape pattern — 643K views): {q_hooks}
- Atmosphere hooks: {seeds_atmos}
- Title patterns (emotional/vulnerable hook preferred — highest CTR for this niche):
{seeds_patterns}
- Real examples of winning titles (competitor research — actual view counts):
  · "Morning Anxiety? 🌱 | Raag Bhairavi inspired Bansuri to Calm Stress & Quiet Overthinking"  ← 643K views
  · "Morning Anxiety? 🌱 | Raag Bhairavi inspired Bansuri (Complete Version) for Calm & Clarity"  ← 195K views
  · "Morning Peace 🌱 | Raag Bhupali inspired Bansuri for Calm Mind & Gentle Focus"  ← 187K views
  · "Too Much Stress? 🌱 | Raag Chandrakauns inspired Sitar for Calm, Clarity & Mental Peace"  ← 53K views
  · "Sitar to Start Your Day | Indian Classical | Music Meditation"  ← 220K views
  · "1 hour of Indian Classical Meditation Music | Sitar for Mental Health"  ← 121K views
  · "Anxiety Wont Go? 🌱 | Raag Yaman inspired Sitar & Bansuri for Stress Relief"  ← 16K views
  · "When Your Mind Won't Sleep 🌙 Raag Darbari Kanada 396Hz | Sitar for Anxiety & Overthinking"
  · "Some Nights Your Mind Won't Slow Down 🌙 Darbari Kanada 396Hz Sitar | Deep Anxiety Relief"

  WINNING PATTERNS (use these frequently):
  1. Question hook: "{{Question}}? {{emoji}} | Raag X inspired {{instrument}} to/for {{benefit}}"
  2. Instrument-first: "{{Instrument}} for {{Mental Health Term}} | Raag X | {{Hz}} Indian Classical"
  3. "1 Hour" explicit: "1 Hour {{Instrument}} | Raag X {{Hz}} | {{Outcome}}"
  4. Emotion hook: "Morning Anxiety / Too Much Stress / Mind Won't Stop" → triggers instant self-identification
- Emotional hook openers for description (pick the most fitting):
{seeds_hooks}

AVOID in title/description: {seeds_avoid}

RECENTLY PUBLISHED (do NOT repeat these angles):
{used_summary}
{locked_section}

TASK: {title_instruction}
Return pure JSON only — no markdown, no extra text.

MUSIC PROMPT GUIDANCE — TWO SEPARATE FIELDS REQUIRED:

① music_prompt  (for Lyria AI — prose sentences, descriptive):
- State instruments, raga, BPM (35-55 for meditation, 40-45 most soothing)
- Include: each note decays with long reverb, wide silence between phrases, no buildup no climax
- Include: warm analog recording quality, loop-friendly structure, deeply meditative
- Specify playing feel: meend glides, komal notes, alap style, how tabla enters
- Anti-patterns: no Western instruments, no percussion fills, no sudden dynamics
- Base on: {schedule['music_hints']}

② suno_style_tags  (for Suno Custom Mode STYLE field — COMMA-SEPARATED TAG STACKS, not sentences):
Suno is a search engine for sound, not ChatGPT. Write tags, not prose.
Follow this exact master formula (DhunDetox brand template):
  Raga {schedule['raga']}, Indian classical instrumental, {schedule['thaat']} thaat, [time of day / season],
  [primary instrument] [playing role], [secondary instrument] [role], [tertiary if any],
  [BPM] BPM, [taal name or "no taal"], alap-jor-jhala structure,
  [3-4 emotional quality tags: e.g. meditative, introspective, spiritual calm, healing resonance],
  cinematic warmth, emotional depth, spiritual stillness,
  high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
  no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade

Special Suno instrument hint tags (always include for these instruments):
  sarangi  → append: "bowed sarangi, crying Indian strings, intimate bowed lute"
  pakhawaj → append: "pakhawaj barrel drum, dhrupad percussion, ancient deep drum"
  mridangam → append: "mridangam South Indian drum, Carnatic rhythm, two-headed drum"
  shehnai  → append: "shehnai reed, ceremonial Indian oboe, nadaswaram style"
  veena    → append: "veena ancient plucked string, Saraswati veena, sustained resonance"

Base on: {schedule['music_hints']}

IMAGE PROMPT GUIDANCE — ILLUSTRATED ART STYLE (Soft Painterly Digital Illustration):

Style: {IMAGE_STYLE_V2}

Generate image_prompt as a soft painterly digital illustration — NOT Madhubani, NOT photorealistic. Think: Indian classical concept art, Artstation quality, storybook illustration, one prominent musician with natural scenic background.

CENTRAL FIGURE (most important — always one musician, always prominent):
- One Indian musician playing {instruments_label} — seated cross-legged, traditional posture
- Face clearly visible, eyes gently closed, serene and meditative expression
- Female musician for string instruments (veena, sitar, sarod), male or female for wind/percussion
- Wearing traditional attire: ornate saree or kurta with subtle embroidery in raga-appropriate colours
- Warm golden glow/halo softly behind the musician's head
- Instrument beautifully detailed, fingers in playing position
- Upper body dominant in frame — musician takes 50-60% of the composition

BACKGROUND SCENE (natural, scenic, time-appropriate):
- {mood_backdrop}
- Derived from schedule image hints: {schedule['image_hints']}
- Soft painterly depth — foreground clear, background impressionist and atmospheric
- Natural elements matching raga and use case "{schedule['use_case']}":
    deep sleep / melatonin → moonlit lake, lotus flowers closed, deer resting, absolute stillness, deep blue-silver
    stress relief / cortisol → golden river at dusk, mango trees, birds settling, warm amber glow
    overthinking / anxiety → monsoon rain on a garden, peacock sheltering, soft candlelight, deep teal
    focus / deep work → moonlit room with latticed window, oil lamp, crescent moon, deep indigo
    morning / cortisol reset → sunrise over river, birds in flight, open terrace, warm saffron-gold
    overactive mind / midnight → midnight garden, crescent moon, oil lamps, deep blue-violet

COLOUR PALETTE — derive from raga and time of day:
    dawn/morning ragas → warm saffron, peach, gold, soft ivory, fresh green
    dusk/evening ragas → amber, rose, peacock teal, warm orange-gold
    night/midnight ragas → deep blue, violet, silver moonlight, warm lamp-gold
    monsoon ragas → deep teal, forest green, grey-rose, bursts of saffron

BORDER AND CLOSING (include word for word):
"Light elegant decorative border on all four edges — thin ornate line with subtle Indian floral and lotus motifs, NOT dense Madhubani pattern coverage. The border is airy and refined, complementing the illustration without overpowering it.
16:9 aspect ratio, concept art quality, 8K detail.
Negative prompt: No text, no title, no words, no watermarks, no logos, no UI elements, no modern objects, no heavy folk art patterns, no dense Madhubani, no anime, no photorealistic CGI, no AI artefacts, no blurry details."

THUMBNAIL PROMPT GUIDANCE (16:9 YouTube thumbnail — illustrated portrait style):
Generate thumbnail_prompt as a SEPARATE composition from the background — optimised for YouTube click-through at small size.

SAME STYLE: soft painterly digital illustration, same as background. NOT Madhubani, NOT photorealistic.

COMPOSITION — portrait style (musician takes 60-70% of frame):
- The {instruments_label} musician close and prominent — upper body and instrument dominant
- Face expressive of the emotional state: furrowed brow dissolving into peace, closed eyes with hint of relief
- Background: atmospheric colour wash — simpler than the background image, soft bokeh nature elements
- The scene immediately tells the viewer what they'll FEEL watching this video

TEXT BANNER — clean and readable (critical for mobile click-through):
A clean ivory/cream parchment scroll or stone tablet naturally integrated in the upper portion of the composition:
  Line 1 (LARGE bold serif, dark ink on ivory/cream background): the thumbnail_hook value — ALL CAPS, max 5 words
  Line 2 (smaller elegant serif): {instruments_label} · Raag {schedule['raga']}
  Bottom strip (small legible serif on a subtle ribbon): the thumbnail_tagline value
The banner must look like it belongs in the scene (a painted scroll, temple plaque, stone inscription) — NOT a digital graphic overlay. Dark text on light background for maximum legibility at small sizes.

COLOUR PALETTE: same as background — raga mood and time of day
  Always: warm golden light touching the musician, inviting and emotional

OUTPUT: write thumbnail_prompt as one flowing paragraph — specific about musician expression, clothing colours, instrument position, banner design, background atmosphere. Make it unique to this raga and use case.

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

☕ Support DhunDetox: buymeacoffee.com/dhundetox
💛 If this music brought you stillness, please LIKE, SUBSCRIBE, and SHARE with someone who needs peace.
🔔 Subscribe to DhunDetox for daily Indian classical healing music, raga therapy, and mindful sound journeys.
💬 Comment below: {{one engaging question for this video's theme}}
🌿 Save this video for when you need it most.

────────────────────────────

⚠️ Disclaimer: This music is intended for relaxation and wellness. Not a substitute for professional medical treatment.

🎵 All music is original and commercially licensed.
Creative direction & visual artwork © DhunDetox.

{hashtag_str}

KEYWORD STRING (separate field — for YouTube tags):
⚠️ HARD LIMIT: Comma-separated, NO spaces after commas, TOTAL MUST BE EXACTLY 470–480 chars.
Count characters before outputting. If over 480 — remove terms. If under 470 — add terms. Do NOT output a string outside this range.
Pattern: raga name variations → instrument + raga combos → instrument alone → meditation/healing/use-case terms → emotion terms → channel name (dhundetox) → 2-3 Hindi keywords at end (e.g. ध्यान संगीत,<instrument> संगीत,राग <raga in Devanagari>).
Do NOT include Hz frequency terms in the keyword string.
PROCESS: Build your list → count total chars → trim/expand to hit 470-480 → output.
Example (count = 475): raag {schedule['raga'].lower()},raga {schedule['raga'].lower()},{instruments_label.replace(' & ', ' ').replace(', ', ' ')},indian classical music,meditation music,healing music,stress relief,sleep music,anxiety relief,deep relaxation,indian raga,classical meditation,relaxing music,mindfulness,dhundetox,ध्यान संगीत,राग {schedule['raga'].lower()}

TAGS GUIDANCE: Target 440–460 chars (YouTube shows 500 but rejects above ~465 in practice). English only. First tag = primary keyword (raag name). Then: raga name variations, instrument+raga combos, instrument alone, broad categories (meditation music, healing music, stress relief), long-tail benefit combos (raag X for anxiety, X meditation), emotion/use-case terms, channel brand (dhundetox) last. Each tag with spaces counts +2 chars toward the budget. Aim for 22–26 quality tags.

{{
  "title": "★★ DEFAULT to Pattern N (Neuroscience formula) — highest performing in niche (Raga Heal: 384K + 368K views). Use Pattern A (question hook) only if Pattern N does not fit naturally. Never default to Pattern D/E/F/G/H.",
  "title_options": [
    "Pattern A — Question hook (643K views): '[Question]? 🌱 | Raag X inspired [Instrument] to/for [benefit]'",
    "Pattern B — Instrument-first (220K views): '[Instrument] for [Mental Health Term] | Raag X | [Hz] Indian Classical'",
    "Pattern C — 1 Hour explicit (121K views): '1 Hour [Instrument] | Raag X [Hz] | [Outcome]'",
    "Pattern D — Benefit-first: 'Melt [use case] | Raag X | Instruments Hz'",
    "Pattern E — Hz-first: '[Hz] [benefit] | Raag X | Instruments [time of day]'",
    "Pattern F — Intent-first: '[Specific intent] | Raga X Instruments | Hz'",
    "Pattern G — Emotional hook: '[Hook] 🌆 Raag X Hz | Instruments [benefit]'",
    "Pattern H — Compressed hook: '[2-word hook] 🌆 Raag X Hz | Instruments [use case]'"
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
  "music_prompt": "Detailed Lyria prose prompt per music guidance above ①",
  "suno_style_tags": "Comma-separated Suno tag stack per music guidance above ②",
  "image_prompt": "Madhubani painting scene per image guidance above",
  "thumbnail_prompt": "16:9 YouTube thumbnail with baked-in text per thumbnail guidance above",
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
