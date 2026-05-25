"""
Studio Step 1 — Draft
Runs the brain (Gemini) and saves today's idea to studio/drafts/YYYY-MM-DD/brain.json.
Then sends a Telegram message so you can review the plan before creating music/image.

Drop these files into studio/drafts/YYYY-MM-DD/ before running --publish:
  clip_1.mp3          (required) your music recording
  clip_2.mp3          (optional) second clip — interleaved with clip_1 to fill 20 min
  background.png/.jpg (required) Madhubani background image (1920x1080 recommended)
  thumbnail.png       (optional) custom thumbnail; if absent, background is used
"""

import html, importlib.util, json, os, sys

STUDIO_DIR  = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR    = os.path.dirname(STUDIO_DIR)
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


def run(client, draft_dir: str) -> dict:
    os.makedirs(draft_dir, exist_ok=True)

    print("[draft] Running brain step...")
    brain_mod = _load_brain_mod()
    brain = brain_mod.run(client)

    brain_path = os.path.join(draft_dir, "brain.json")
    with open(brain_path, "w", encoding="utf-8") as f:
        json.dump(brain, f, indent=2, ensure_ascii=False)
    print(f"[draft] Saved -> {brain_path}")

    def e(s): return html.escape(str(s))
    date_label = os.path.basename(draft_dir)
    msg = (
        f"\U0001f3b5 <b>DhunDetox — Idea of the Day</b>\n\n"
        f"\U0001f3bc <b>Raga:</b> {e(brain.get('raga', '—'))}\n"
        f"\U0001fa98 <b>Instruments:</b> {e(brain.get('instrument', '—'))}\n"
        f"\U0001f3af <b>Use case:</b> {e(brain.get('use_case', '—'))}\n\n"
        f"\U0001f4cc <b>Title:</b>\n{e(brain.get('title', '—'))}\n\n"
        f"\U0001f4a1 <b>Hook angle:</b> {e(brain.get('hook_angle', '—'))}\n\n"
        f"\U0001f5bc <b>Thumbnail hook:</b> {e(brain.get('thumbnail_hook', '—'))}\n"
        f"\U0001f516 <b>Tagline:</b> {e(brain.get('thumbnail_tagline', '—'))}\n\n"
        f"\U0001f3ac <b>Music prompt (preview):</b>\n"
        f"<i>{e(brain.get('music_prompt', '')[:200])}...</i>\n\n"
        f"\U0001f4c1 Drop your files into:\n"
        f"<code>studio/drafts/{date_label}/</code>\n"
        f"  clip_1.mp3  (required)\n"
        f"  clip_2.mp3  (optional)\n"
        f"  background.png  (required)\n"
        f"  thumbnail.png   (optional)\n\n"
        f"Then run:\n"
        f"<code>python studio/orchestrator.py --publish</code>"
    )
    tg.send_text(msg)
    print("[draft] Telegram notification sent.")

    return brain
