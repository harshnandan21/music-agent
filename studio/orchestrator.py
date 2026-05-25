"""
Studio Orchestrator — two-phase manual workflow

Phase 1 (--draft):
  Runs the brain (Gemini) → saves idea to studio/drafts/YYYY-MM-DD/brain.json
  → sends a Telegram message with today's idea so you can create music + image.

Phase 2 (--publish):
  Reads the draft folder → extends your music clips to 20 min → assembles video
  → sends Telegram preview with APPROVE / REJECT buttons → uploads on approval.

Usage:
  python studio/orchestrator.py --draft
  python studio/orchestrator.py --publish
  python studio/orchestrator.py --publish --date 2026-05-25

Before running --publish, drop into studio/drafts/YYYY-MM-DD/:
  clip_1.mp3       (required) your recorded music
  clip_2.mp3       (optional) second clip — interleaved with clip_1
  background.png   (required) 1920x1080 Madhubani background
  thumbnail.png    (optional) custom thumbnail
"""

import importlib.util, json, os, sys, traceback
from datetime import date

STUDIO_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
STEPS_DIR  = os.path.join(STUDIO_DIR, "steps")

sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, STUDIO_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from google import genai
from config import GEMINI_API_KEY
import studio.telegram as tg


def _load_step(filename: str):
    """Load a steps/ module by filename (handles digit-prefixed names)."""
    name = os.path.splitext(filename)[0]
    spec = importlib.util.spec_from_file_location(name, os.path.join(STEPS_DIR, filename))
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _get_date_arg() -> str:
    for i, arg in enumerate(sys.argv):
        if arg == "--date" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return str(date.today())


def _draft_dir(date_str: str) -> str:
    return os.path.join(STUDIO_DIR, "drafts", date_str)


def _load_brain(draft_dir: str) -> dict:
    brain_path = os.path.join(draft_dir, "brain.json")
    if not os.path.exists(brain_path):
        raise FileNotFoundError(f"brain.json not found in {draft_dir}. Run --draft first.")
    with open(brain_path, encoding="utf-8") as f:
        return json.load(f)


# ── Phase 1 ───────────────────────────────────────────────────────────────────

def do_draft(date_str: str):
    print("=" * 60)
    print(f"STUDIO — Draft  ({date_str})")
    print("=" * 60)

    draft_dir = _draft_dir(date_str)
    client    = genai.Client(api_key=GEMINI_API_KEY)

    step01 = _load_step("01_draft.py")
    _, decision = step01.run(client, draft_dir)

    print("=" * 60)
    if decision == "rejected":
        print("Idea rejected via Telegram. Re-run --draft to generate a new one.")
    else:
        print(f"Draft saved: {draft_dir}")
        print("Idea approved! Drop your files and run --publish when ready.")
    print("=" * 60)


# ── Phase 2 ───────────────────────────────────────────────────────────────────

def do_publish(date_str: str):
    print("=" * 60)
    print(f"STUDIO — Publish  ({date_str})")
    print("=" * 60)

    draft_dir = _draft_dir(date_str)
    brain     = _load_brain(draft_dir)
    title_safe = brain.get('title', '').encode('ascii', 'replace').decode('ascii')
    print("[orchestrator] Title:", title_safe)

    tg.send_text(f"Publish started for {date_str}\n{title_safe}")

    # Step 2 — Extend music (skip if music.mp3 already exists)
    music_path = os.path.join(draft_dir, "music.mp3")
    if os.path.exists(music_path):
        print(f"[orchestrator] music.mp3 already present — skipping extend step.")
        tg.send_text("music.mp3 already exists — skipping extend step.")
    else:
        tg.send_text("Extending music clips to 20+ min... (takes 3-5 min)")
        step02 = _load_step("02_extend.py")
        step02.run(draft_dir)
        tg.send_text("Music ready.")

    # Step 3 — Assemble video (skip if video.mp4 already exists)
    video_path = os.path.join(draft_dir, "video.mp4")
    if os.path.exists(video_path):
        print(f"[orchestrator] video.mp4 already present — skipping assemble step.")
        tg.send_text("video.mp4 already exists — skipping assemble step.")
    else:
        tg.send_text("Assembling video (image + music)... (takes 2-4 min)")
        step03 = _load_step("03_assemble.py")
        step03.run(brain, draft_dir)
        tg.send_text("Video assembled. Sending for approval...")

    # Telegram approval
    preview_image = None
    for name in ["thumbnail.png", "thumbnail.jpg", "background.png", "background.jpg"]:
        p = os.path.join(draft_dir, name)
        if os.path.exists(p):
            preview_image = p
            break

    token   = tg.new_token()
    caption = (
        f"Ready to upload?\n\n"
        f"Raga: {brain.get('raga', '—')}\n"
        f"Instruments: {brain.get('instrument', '—')}\n\n"
        f"Title:\n{brain.get('title', '—')}\n\n"
        f"Hook: {brain.get('thumbnail_hook', '—')}\n"
        f"Tagline: {brain.get('thumbnail_tagline', '—')}"
    )
    tg.send_approval(preview_image, caption, token)
    decision = tg.wait_for_decision(token, timeout_seconds=21600)

    if decision == "rejected":
        print("[orchestrator] Upload rejected via Telegram. Files kept in draft folder.")
        sys.exit(0)

    # Step 4 — Upload
    step04 = _load_step("04_upload.py")
    video_id = step04.run(brain, draft_dir)

    tg.send_text(
        f"\U0001f389 Uploaded!\n\n"
        f"{brain.get('title', '')}\n\n"
        f"https://youtu.be/{video_id}"
    )
    print("=" * 60)
    print(f"DONE — https://youtu.be/{video_id}")
    print("=" * 60)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    date_str = _get_date_arg()

    if "--draft" in sys.argv:
        try:
            do_draft(date_str)
        except Exception as e:
            print(f"\n[ERROR] Draft failed: {e}")
            traceback.print_exc()
            sys.exit(1)
    elif "--publish" in sys.argv:
        try:
            do_publish(date_str)
        except Exception as e:
            print(f"\n[ERROR] Publish failed: {e}")
            traceback.print_exc()
            sys.exit(1)
    else:
        print(__doc__)
        print("Error: pass --draft or --publish")
        sys.exit(1)


if __name__ == "__main__":
    main()
