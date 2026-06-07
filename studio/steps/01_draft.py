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
    return f"VEO — VIDEO PROMPT (8-second seamless loop)\n\n{brain.get('video_prompt', '')}"


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

    # 1 — Idea summary with APPROVE / REJECT
    caption = (
        f"DhunDetox — Idea of the Day ({date_label})\n\n"
        f"Raga: {brain.get('raga', '—')}\n"
        f"Instruments: {brain.get('instrument', '—')}\n"
        f"Use case: {brain.get('use_case', '—')}\n\n"
        f"Title:\n{brain.get('title', '—')}\n\n"
        + (
            "Other title options:\n"
            + "\n".join(f"  {i+1}. {t}" for i, t in enumerate(brain.get("title_options", [])))
            + "\n\n"
            if brain.get("title_options") else ""
        )
        + f"Hook: {brain.get('thumbnail_hook', '—')}\n"
        f"Tagline: {brain.get('thumbnail_tagline', '—')}\n\n"
        f"Approve to lock in today's idea."
    )
    token = tg.new_token()
    tg.send_approval(None, caption, token)

    # 2 — All prompts as a single .txt file (open on phone → easy copy-paste)
    suno  = _suno_prompt(brain)
    bg    = _gemini_bg_prompt(brain)
    video = _veo_video_prompt(brain)
    divider = "\n" + "=" * 60 + "\n\n"
    doc_content = (
        f"DHUNDETOX — IDEA OF THE DAY ({date_label})\n"
        f"{'=' * 60}\n\n"
        f"Raga:        {brain.get('raga', '')}\n"
        f"Instruments: {brain.get('instrument', '')}\n"
        f"Title:       {brain.get('title', '')}\n"
        + (
            "".join(f"  Option {i+1}: {t}\n" for i, t in enumerate(brain.get("title_options", [])))
            if brain.get("title_options") else ""
        )
        + f"Hz:          {brain.get('hz_frequency', '')}\n"
        f"Hook:        {brain.get('thumbnail_hook', '')}\n"
        f"Tagline:     {brain.get('thumbnail_tagline', '')}\n"
        + divider
        + suno
        + divider
        + bg
        + divider
        + video
        + "\n"
    )
    tg.send_document(
        filename=f"dhundetox-{date_label}.txt",
        content=doc_content,
        caption=f"Open file to copy Suno + Gemini prompts",
    )

    print("[draft] Prompts sent. Waiting up to 10h for approval (no reply = rejected)...")
    decision = tg.wait_for_decision(token, timeout_seconds=36000)
    if decision == "timeout":
        decision = "rejected"
    print(f"[draft] Decision: {decision}")

    if decision == "approved":
        tg.send_text(
            f"Idea locked in for {date_label}!\n\n"
            f"Drop your files into studio/drafts/{date_label}/\n"
            f"  clip_1.mp3      (required)\n"
            f"  clip_2.mp3      (optional)\n"
            f"  background.png  (required)\n"
            f"  thumbnail.png   (optional)\n\n"
            f"Then run:\npython studio/orchestrator.py --publish"
        )
        # Offer automation: run full automated pipeline into the draft folder
        try:
            choice_token = tg.new_token()
            tg.send_choice_prompt(choice_token,
                "<b>Would you like to automate generation now?</b>\nGenerate music, image, assemble & upload automatically.",
                [("⚡ Automate now", "AUTOMATE"), ("📝 Manual — I'll add files", "MANUAL")]
            )
            choice = tg.wait_for_choice(choice_token, timeout_seconds=3600)
            if choice == "AUTOMATE":
                tg.send_text("Starting automated generation now — I'll report back when done.")
                try:
                    import studio.auto_publish as auto_pub
                    auto_pub.run(brain, draft_dir)
                    tg.send_text("Automated pipeline finished. Check draft folder or YouTube for result.")
                    decision = "automated"
                except Exception as e:
                    tg.send_text(f"Automation failed: {e}")
            else:
                tg.send_text("OK — keep files in the draft folder and run --publish when ready.")
        except Exception:
            # Non-fatal — keep original manual instructions
            pass
    else:
        tg.send_text(f"Idea for {date_label} rejected / timed out. Run --draft again for a new idea.")

    return brain, decision
