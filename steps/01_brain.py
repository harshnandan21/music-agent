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
    CONTENT_SEEDS, MADHUBANI_STYLE, CINEMATIC_STYLE,
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
    for key in ("hz_frequency", "title", "thumbnail_hook", "thumbnail_instr", "thumbnail_tagline", "hook_phrase"):
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

    seeds_outcomes  = ", ".join(CONTENT_SEEDS["outcome_hooks"][:10])
    seeds_atmos     = ", ".join(CONTENT_SEEDS["atmosphere_hooks"][:8])
    seeds_patterns  = "\n".join(f"  · {p}" for p in CONTENT_SEEDS["title_patterns"])
    seeds_hooks     = "\n".join(f"  · {p}" for p in CONTENT_SEEDS["hook_phrases"][:6])
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

VIDEO PROMPT GUIDANCE (for Veo — seamless 8-second loop):
- Animation elements reference: {VIDEO_ANIMATION_GUIDE}
- Camera completely static. Only natural elements animate (stars, water, smoke, flames).
- Base on the image scene: choose the matching animation type from the guide.

DESCRIPTION TEMPLATE — follow this structure exactly:

{emoji matching use case} {{SEO title repeat}}

{{2-3 sentence hook: address the pain point directly, short and punchy}}

This deeply meditative composition in **Raag {schedule['raga']}** blends the healing resonance of **{{hz_frequency}}** — known for {{hz benefit}} — with soulful **{instruments_label}** to {{use case benefits}}.

> *"{{hook_phrase}}"*

{{2-3 sentences: cultural/historical context of Raag {schedule['raga']}, what it does to the nervous system}}

**{{emoji}} Perfect for:**
- {{8 specific use cases as bullet points}}

**🎵 Why Raag {schedule['raga']} heals:**
{{2-3 sentences: parasympathetic nervous system, raga science, Hz frequency benefit if applicable}}

**🎧 How to use this music:**
1. Use headphones at a comfortable, low volume
2. Dim the lights or turn them off completely
3. Lie down or sit comfortably with eyes closed
4. Take 3 slow deep breaths — exhale longer than you inhale
5. Let the {{primary instrument}} guide your thoughts into softness
6. Let the {{secondary instrument}} slow your breath
7. Let the {{third instrument or rhythm}} ground you in peace
8. Stay for at least 15–20 minutes for the full effect

---

**🇮🇳 हिंदी में:**
{{3-4 lines in Hindi describing raga, instruments, use case}}
*"{{hook_phrase translated to Hindi}}"*

---

💛 If this music brought you stillness tonight, please **LIKE, SUBSCRIBE, and SHARE** with someone who needs peace.
🔔 **Subscribe to DhunDetox** for more healing frequencies, Indian classical meditation music, raga therapy, and mindful sound journeys.
💬 Comment below: *{{engaging question related to this video's theme}}*
🌿 **Save this video** for when you need it most.

---

⚠️ *Disclaimer: This music is intended for relaxation, meditation, and wellness purposes. It is not a substitute for professional medical or psychological treatment.*

{hashtag_str}

KEYWORD STRING (separate field — for YouTube tags):
Comma-separated, no spaces after commas, total 490–500 chars exactly.
Pattern: raga name variations, instruments, hz frequency variants, use case terms, channel name (dhundetox).
Example: raag {schedule['raga'].lower()},raga {schedule['raga'].lower()},{instruments_label.replace(' & ', ' ').replace(', ', ' ')},396hz,396 hz healing,...,dhundetox

TAGS GUIDANCE: Exactly 15 tags max — English only, each max 30 chars, total under 400 chars combined. Parse from the keyword string above.

{{
  "title": "SEO title ≤70 chars",
  "description": "Full YouTube description following the 11-section template above, including Hindi section, CTA, disclaimer, and 15 hashtags at end",
  "keywords": "comma-separated keyword string, 490-500 chars, no spaces after commas, for YouTube tags field",
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
    print(f"[brain] Raga={data['raga']} | Instruments={data['instrument']} | Hz={locked.get('hz_frequency', 'none')}")
    print(f"[brain] Title: {data['title']}")
    print(f"[brain] Hook: {data.get('thumbnail_hook')} | Tagline: {data.get('thumbnail_tagline')}")
    return data


if __name__ == "__main__":
    import pprint
    from google import genai as _genai
    _client = _genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    pprint.pprint(run(_client))
