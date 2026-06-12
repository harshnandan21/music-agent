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

    # STYLE — use Suno-optimised tag stack; fall back to music_prompt prose if missing
    style = brain.get("suno_style_tags") or brain.get("music_prompt", "")

    # LYRICS — vary structure by content category
    category = brain.get("suno_lyrics_style", brain.get("playlist", "stress"))

    if category == "sleep":
        lyrics = (
            f"[Opening — pure silence, then {instr1} enters with a single note]\n"
            f"[Sparse alap — each phrase 8-10 seconds apart, tanpura drone beneath]\n\n"
            f"[Vilambit — progressively slower, each note fading before the next]\n"
            f"[Deep Stillness — phrases becoming whispers, vast silence between]\n\n"
            f"[Final fade — no resolution, sound dissolving into quiet]"
        )
    elif category == "morning":
        lyrics = (
            f"[Gentle Alap — {instr1} opens softly, ascending phrases like sunrise]\n"
            f"[Awakening — warmth building, not urgency, a slow opening]\n\n"
            f"[Madhya Laya — mid-pace steady energy, {(instr2 or instr1)} enters]\n"
            f"[Open Flow — brightness without force, breathing with the music]\n\n"
            f"[Gentle Close — leave room to start the day, no dramatic ending]"
        )
    elif category == "focus":
        lyrics = (
            f"[Slow Alap — {instr1} solo, methodical, each phrase deliberate]\n"
            f"[Deep Concentration — wide silence between phrases, thought completing itself]\n\n"
            f"[Vilambit Gat — sparse rhythm enters, laser stillness, no distraction]\n"
            f"[Extended Flow — sustained clarity, no climax, no break in concentration]\n\n"
            f"[Open Awareness — no resolution, just sustained focus]"
        )
    elif category == "midnight":
        lyrics = (
            f"[Heavy Alap — {instr1} alone, gravity in every note, 10-second silences]\n"
            f"[Deliberate Stillness — thoughts settling like sediment, no hurry]\n\n"
            f"[Slow Gat — rhythm enters at 3+ minutes, minimal, ancient pulse]\n"
            f"[Sustained Meditation — no buildup, no climax, just the midnight]\n\n"
            f"[Fade into silence — the music becomes the room, then nothing]"
        )
    else:  # stress / anxiety (default)
        lyrics = (
            f"[Slow Alap — {instr1} enters alone, no rhythm, emotional release begins]\n"
            f"[Komal phrases — longing held, then released, like exhaling weeks of tension]\n\n"
            f"[Gentle Gat — rhythm enters softly, breath-paced, {(instr2 or instr1)} joins]\n"
            f"[Emotional Release — phrases that sigh and resolve, the weight lifting]\n\n"
            f"[Fade — cortisol dropping, nervous system finally resting]"
        )

    return (
        f"SUNO CUSTOM MODE\n\n"
        f"STYLE FIELD (paste exactly — comma-separated tag stacks, not sentences):\n{style}\n\n"
        f"LYRICS FIELD (structural markers — controls arrangement):\n{lyrics}\n\n"
        f"TIPS:\n"
        f"· Instrumental toggle → ON (always)\n"
        f"· Generate 4-6 variations, pick the 2 with the most silence and gravity\n"
        f"· Use Extend 2-3× to reach 60 minutes\n"
        f"· Run the best clip through Remaster for cleaner audio\n"
        f"· Use Inpainting to fix weak sections (e.g. if tabla drops out unnaturally)\n"
        f"· Download stems → layer/refine in Audacity or GarageBand if needed\n"
        f"· Avoid clips that build to a dramatic climax or have Western percussion\n"
        f"· If rare instrument sounds wrong, add 'no violin, no orchestra' to Style"
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
    suno  = _suno_prompt(brain)
    bg    = _gemini_bg_prompt(brain)
    video = _veo_video_prompt(brain)

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
