"""
Studio Step 1 — Draft
Runs the brain (Gemini), saves brain.json, sends Telegram with idea summary
(APPROVE/REJECT) + full Suno and Gemini prompts as follow-up messages.
Waits up to 10 hours for approval before auto-rejecting.
"""

import importlib.util, json, os, sys

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "steps"))

import studio.telegram as tg


def _load_brain_mod():
    spec = importlib.util.spec_from_file_location(
        "brain", os.path.join(ROOT_DIR, "steps", "01_brain.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_instruments(instrument_str: str) -> list[str]:
    parts = [p.strip() for p in instrument_str.replace(" & ", ",").replace(" and ", ",").split(",")]
    return [p for p in parts if p]


def _suno_prompt(brain: dict) -> str:
    parts  = _parse_instruments(brain.get("instrument", "sitar"))
    instr1 = parts[0] if parts else "sitar"
    instr2 = parts[1] if len(parts) > 1 else ""

    base = brain.get("suno_style_tags") or brain.get("music_prompt", "")
    cat  = brain.get("suno_lyrics_style", brain.get("playlist", "stress"))

    # ── Energy-level style modifiers ──────────────────────────────────────
    sparse_mod = (
        f"solo {instr1} dominant, no tabla, "
        + (f"no {instr2}, " if instr2 else "")
        + "ultra slow 30 BPM, vast silence between phrases, "
        "alap only, no rhythm section, extreme stillness, long pauses"
    )
    medium_mod = (
        f"{instr1} leads, "
        + (f"{instr2} enters gently, " if instr2 else "")
        + "tabla 40 BPM very soft, sparse gat, trio building slowly, "
        "meditative flow, measured pace, no climax"
    )
    full_mod = (
        f"full trio peak, {instr1} freely flowing, "
        + (f"{instr2} warm resonance, " if instr2 else "")
        + "tabla conversational 48 BPM, complete alap-jor-jhala arc, "
        "musical conversation, flowing energy"
    )

    # ── Simple bracket lyrics per energy level + category ─────────────────
    sparse_v1 = "[Solo Alap]\n[Long Silence]\n\n[Single Phrase]\n[Stillness]"
    sparse_v2 = "[Opening Note]\n[Vast Silence]\n\n[Slow Alap]\n[Fade Into Quiet]"

    if cat == "morning":
        medium_v1 = "[Trio Enters]\n[Gentle Gat]\n\n[Steady Flow]\n[Morning Light]"
        medium_v2 = "[Awakening]\n[Soft Rhythm]\n\n[Open Flow]\n[Gentle Brightness]"
        full_v1   = "[Full Trio]\n[Morning Peak]\n\n[Flowing Energy]\n[Gentle Close]"
        full_v2   = "[Complete Arc]\n[Madhya Laya]\n\n[Conversational]\n[Warm Ending]"
    elif cat == "sleep":
        medium_v1 = "[Drone Deepens]\n[Slow Gat]\n\n[Dissolving]\n[Deep Stillness]"
        medium_v2 = "[Sparse Entry]\n[Night Rhythm]\n\n[Fading]\n[Silence]"
        full_v1   = "[Full Night]\n[Deep Meditation]\n\n[Dissolving]\n[Final Fade]"
        full_v2   = "[Vilambit]\n[Night Peak]\n\n[Slow Dissolution]\n[Into Silence]"
    elif cat == "focus":
        medium_v1 = "[Trio Enters]\n[Deliberate Gat]\n\n[Concentration]\n[Sustained Flow]"
        medium_v2 = "[Methodical]\n[Sparse Rhythm]\n\n[Clarity]\n[Extended Focus]"
        full_v1   = "[Full Clarity]\n[Peak Focus]\n\n[No Distraction]\n[Open Awareness]"
        full_v2   = "[Deep Work]\n[Sustained]\n\n[Laser Stillness]\n[Focused Close]"
    elif cat == "midnight":
        medium_v1 = "[Midnight Gat]\n[Ancient Pulse]\n\n[Heavy Stillness]\n[Sustained]"
        medium_v2 = "[Slow Entry]\n[Night Rhythm]\n\n[Contemplation]\n[Settling]"
        full_v1   = "[Full Midnight]\n[Deep Meditation]\n\n[No Climax]\n[Fade Into Dark]"
        full_v2   = "[Complete Arc]\n[Midnight Peak]\n\n[Vilambit]\n[Into Nothing]"
    else:  # stress / anxiety (default)
        medium_v1 = "[Trio Enters]\n[Gentle Gat]\n\n[Emotional Release]\n[Weight Lifting]"
        medium_v2 = "[Soft Rhythm]\n[Breath-Paced]\n\n[Sighing Phrases]\n[Resolve]"
        full_v1   = "[Full Trio]\n[Steady Flow]\n\n[Complete Release]\n[Nervous System Rest]"
        full_v2   = "[Musical Conversation]\n[Peak Flow]\n\n[Settling]\n[Cortisol Drop]"

    def _clip(n, style_mod, lyrics, label):
        return (
            f"── CLIP {n} ({label}) ──────────────────────────────\n"
            f"STYLE FIELD:\n{base}, {style_mod}\n\n"
            f"LYRICS FIELD:\n{lyrics}\n"
        )

    clips = "\n".join([
        _clip(1, sparse_mod, sparse_v1, "SPARSE var 1  → save as 1.wav"),
        _clip(2, sparse_mod, sparse_v2, "SPARSE var 2  → save as 2.wav"),
        _clip(3, medium_mod, medium_v1, "MEDIUM var 1  → save as 3.wav"),
        _clip(4, medium_mod, medium_v2, "MEDIUM var 2  → save as 4.wav"),
        _clip(5, full_mod,   full_v1,   "FULL var 1    → save as 5.wav"),
        _clip(6, full_mod,   full_v2,   "FULL var 2    → save as 6.wav"),
    ])

    return (
        f"SUNO CUSTOM MODE — 6 CLIPS (3 energy levels × 2 variations)\n"
        f"Instrumental toggle → ON for all clips.\n"
        f"{'=' * 60}\n\n"
        f"{clips}\n"
        f"{'=' * 60}\n"
        f"TIPS:\n"
        f"· SPARSE (1-2): solo {instr1}, no rhythm — alap-like, long silences\n"
        f"· MEDIUM (3-4): trio building, tabla very soft 40 BPM\n"
        f"· FULL (5-6):   full trio peak, tabla 48 BPM\n"
        f"· Remaster each clip after generating\n"
        f"· Drop all 6 in draft folder — pipeline loops to natural 60-70 min\n"
        f"· Avoid dramatic climax or Western percussion"
    )


def _gemini_bg_prompt(brain: dict) -> str:
    title    = brain.get("title", "")
    hook     = brain.get("thumbnail_hook", "")
    tagline  = brain.get("thumbnail_tagline", "")
    prompt   = brain.get("image_prompt", "")
    preamble = (
        f"GEMINI PRO — BACKGROUND IMAGE (16:9)\n\n"
        f"Context for this image:\n"
        f"  Video title:  {title}\n"
        f"  Hook:         {hook}\n"
        f"  Tagline:      {tagline}\n\n"
        f"The image must visually express the emotional state of the title above.\n"
        f"A viewer should FEEL the use case just from looking — no text needed.\n\n"
        f"IMAGE PROMPT:\n{prompt}"
    )
    return preamble


def _thumbnail_prompt(brain: dict) -> str:
    hook    = brain.get("thumbnail_hook", "")
    instr   = brain.get("thumbnail_instr", "")
    tagline = brain.get("thumbnail_tagline", "")
    title   = brain.get("title", "")
    prompt  = brain.get("thumbnail_prompt", "")
    return (
        f"GEMINI PRO — THUMBNAIL (16:9, baked-in text)\n\n"
        f"Context:\n"
        f"  Video title: {title}\n"
        f"  Hook text:   {hook}\n"
        f"  Instr line:  {instr}\n"
        f"  Tagline:     {tagline}\n\n"
        f"TEXT TO BAKE IN (render as part of the painting, not a label):\n"
        f"  Line 1 (large bold serif):  {hook}\n"
        f"  Line 2 (smaller serif):     {instr}\n"
        f"  Bottom strip:               {tagline}\n\n"
        f"IMAGE PROMPT:\n{prompt}"
    )


def _veo_video_prompt(brain: dict) -> str:
    """Generate 4 Gemini Animation Blueprint prompts from brain.json video_prompt."""
    video_prompt = brain.get("video_prompt", "")

    # Parse animated elements from the "Only animate these subtle elements:" bullet list
    elements = []
    in_section = False
    for line in video_prompt.split("\n"):
        if "only animate" in line.lower() or "animate these" in line.lower():
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith("-"):
                element = stripped.lstrip("- ").split(":")[0].strip()
                elements.append(element)
            elif stripped and not stripped.startswith("-"):
                in_section = False

    if not elements:
        return f"VEO — VIDEO PROMPTS\n\nBase prompt:\n{video_prompt}"

    # All elements except the current one — used in the "freeze" sentence
    all_frozen = "musicians, instruments, temple, sky, border patterns, and all other elements"

    clips = []
    for i, element in enumerate(elements[:4], 1):
        others = [e for j, e in enumerate(elements[:4]) if j != i - 1]
        freeze_list = ", ".join(others) + (", " if others else "") + "musicians, instruments, temple, sky, and all Madhubani border patterns"
        clips.append(
            f"CLIP {i} (clip_{i}.mp4):\n"
            f"Only {element} animate subtly. "
            f"The {freeze_list} remain completely frozen like a painting. "
            f"Static camera. 8-second seamless loop."
        )

    divider = "\n\n"
    return (
        f"VEO — VIDEO PROMPTS (Gemini Videos tab)\n"
        f"Upload background.png as source image for EACH clip.\n"
        f"{'=' * 50}\n\n"
        + divider.join(clips)
    )


def _print_draft(brain: dict, date_label: str):
    """Print full idea summary + all prompts to terminal."""
    SEP = "=" * 60
    suno      = _suno_prompt(brain)
    bg        = _gemini_bg_prompt(brain)
    thumbnail = _thumbnail_prompt(brain)
    video     = _veo_video_prompt(brain)

    title_opts = brain.get("title_options", [])
    print(f"\n{SEP}")
    print(f"DHUNDETOX — IDEA OF THE DAY ({date_label})")
    print(SEP)
    print(f"Raga:        {brain.get('raga', '')}")
    print(f"Instruments: {brain.get('instrument', '')}")
    print(f"Hz:          {brain.get('hz_frequency', '')}")
    print(f"Use case:    {brain.get('use_case', '')}")
    print(f"\nTitle: {brain.get('title', '')}")
    if title_opts:
        print("\nOther title options:")
        for i, t in enumerate(title_opts):
            print(f"  {i+1}. {t}")
    print(f"\nHook:    {brain.get('thumbnail_hook', '')}")
    print(f"Tagline: {brain.get('thumbnail_tagline', '')}")
    print(f"\n{SEP}\n")
    print(suno)
    print(f"\n{SEP}\n")
    print(bg)
    print(f"\n{SEP}\n")
    print(thumbnail)
    print(f"\n{SEP}\n")
    print(video)
    print(f"\n{SEP}")
    print(f"Drop files into: studio/drafts/{date_label}/")
    print(f"Then run: python studio/orchestrator.py --publish --date {date_label}")
    print(SEP)


def run(client, draft_dir: str) -> tuple[dict, str]:
    os.makedirs(draft_dir, exist_ok=True)
    date_label = os.path.basename(draft_dir)

    print("[draft] Running brain step...")
    brain_mod = _load_brain_mod()
    brain = brain_mod.run(client)

    brain_path = os.path.join(draft_dir, "brain.json")
    with open(brain_path, "w", encoding="utf-8") as f:
        json.dump(brain, f, indent=2, ensure_ascii=False)
    print(f"[draft] Saved -> {brain_path}")

    _print_draft(brain, date_label)
    return brain, "approved"
