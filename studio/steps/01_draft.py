"""
Studio Step 1 — Draft
Runs the brain (Gemini), saves brain.json, sends Telegram with idea summary
(APPROVE/REJECT) + full Suno and Gemini prompts as follow-up messages.
Waits up to 2 hours for approval before the day's work begins.
"""

import html, importlib.util, json, os, sys

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
    raga   = brain.get("raga", "Unknown")
    parts  = _parse_instruments(brain.get("instrument", "sitar"))
    instr1 = parts[0] if parts else "sitar"
    instr2 = parts[1] if len(parts) > 1 else ""

    nocturnal_ragas = {"chandrakauns", "darbari", "bageshri", "yaman", "bhairavi", "malkauns", "kedar"}
    time_tag = "nocturnal raga" if any(w in raga.lower() for w in nocturnal_ragas) else "meditative raga"

    style_parts = [
        "Indian classical instrumental",
        f"Raag {raga}",
        f"{instr1} lead",
    ]
    if instr2:
        style_parts.append(f"{instr2} accompaniment")
    style_parts += [
        "45 BPM", time_tag,
        "analog warmth", "long reverb tails",
        "sparse arrangement", "no vocals",
        "no Western instruments", "loop-friendly",
    ]

    lyrics = (
        f"[Slow Alap - {instr1.title()} Solo]\n"
        f"[Deep meditative phrases, wide silences, komal notes held long]\n\n"
        f"[Vilambit Gat - {(instr2 or instr1).title()} enters]\n"
        f"[Sparse rhythm, {instr1} melody introspective and grave]\n\n"
        f"[Extended Meditation]\n"
        f"[No climax, no resolution — sustained stillness, each phrase completing itself]\n\n"
        f"[Fade into silence]"
    )

    return (
        f"SUNO CUSTOM MODE\n\n"
        f"STYLE FIELD:\n{', '.join(style_parts)}\n\n"
        f"LYRICS FIELD:\n{lyrics}\n\n"
        f"TIP: Generate 2-3 clips. Use the one with the most silence and gravity. "
        f"Avoid clips that build to a dramatic climax."
    )


def _gemini_bg_prompt(brain: dict) -> str:
    return f"GEMINI PRO — BACKGROUND IMAGE (16:9)\n\n{brain.get('image_prompt', '')}"


def _gemini_thumb_prompt(brain: dict) -> str:
    parts  = _parse_instruments(brain.get("instrument", "sitar"))
    instr1 = parts[0] if parts else "sitar"
    hook   = brain.get("thumbnail_hook", "")
    tagline = brain.get("thumbnail_tagline", "")
    mood   = brain.get("hook_angle", "")

    return (
        f"GEMINI PRO — THUMBNAIL (16:9, YouTube-optimised)\n\n"
        f"Create a bold, high-contrast YouTube thumbnail in Madhubani folk art style. "
        f"16:9 format, must look striking at 320x180px.\n\n"
        f"Composition: Left 60% — deep indigo night sky, large glowing full moon upper half, "
        f"ornate {instr1} dead-centre slightly oversized, gold lotus decoration, warm saffron lamp glow from below. "
        f"Right 40% — intentionally darker and simpler, faint peacock silhouette and geometric border, "
        f"clear space for text overlay.\n\n"
        f"Style: Madhubani flat illustration, thick black outlines, no gradients, no photorealism, "
        f"no 3D shading. Bold and graphic.\n\n"
        f"Mood: {mood}\n\n"
        f"Text to overlay later (do NOT include in image) — Hook: {hook} | Tagline: {tagline}\n\n"
        f"No text, no watermarks, no letters anywhere. Pure illustration only."
    )


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
        f"Hook: {brain.get('thumbnail_hook', '—')}\n"
        f"Tagline: {brain.get('thumbnail_tagline', '—')}\n\n"
        f"Approve to lock in today's idea."
    )
    token = tg.new_token()
    tg.send_approval(None, caption, token)

    # 2 — Full Suno prompt
    def e(s): return html.escape(str(s))
    suno = _suno_prompt(brain)
    tg.send_text(f"<b>SUNO CUSTOM MODE</b>\n\n<pre>{e(suno)}</pre>")

    # 3 — Gemini background prompt
    bg = _gemini_bg_prompt(brain)
    tg.send_text(f"<b>GEMINI — BACKGROUND (16:9)</b>\n\n<pre>{e(bg[:3800])}</pre>")

    # 4 — Gemini thumbnail prompt
    thumb = _gemini_thumb_prompt(brain)
    tg.send_text(f"<b>GEMINI — THUMBNAIL</b>\n\n<pre>{e(thumb[:3800])}</pre>")

    print("[draft] Prompts sent. Waiting up to 2h for approval...")
    decision = tg.wait_for_decision(token, timeout_seconds=7200)
    print(f"[draft] Decision: {decision}")

    if decision == "approved":
        tg.send_text(
            f"Idea locked in for {date_label}!\n\n"
            f"Drop your files into studio/drafts/{date_label}/\n"
            f"  clip_1.mp3   (required)\n"
            f"  clip_2.mp3   (optional)\n"
            f"  background.png  (required)\n"
            f"  thumbnail.png   (optional)\n\n"
            f"Then run:\npython studio/orchestrator.py --publish"
        )

    return brain, decision
