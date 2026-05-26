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
  clip.mp4         (optional) 8-second Veo loop — preferred over background image
  background.png   (required if no clip.mp4) 1920x1080 Madhubani background
  thumbnail.png    (optional) custom thumbnail
"""

import importlib.util, json, os, shutil, sys, traceback
from datetime import date, timedelta

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

    draft_dir  = _draft_dir(date_str)
    brain_path = os.path.join(draft_dir, "brain.json")
    if os.path.exists(brain_path) and "--force" not in sys.argv:
        print(f"[orchestrator] brain.json already exists for {date_str}. Use --force to regenerate.")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)

    step01 = _load_step("01_draft.py")

    MAX_RETRIES = 3
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            print(f"[orchestrator] Generating new idea (attempt {attempt}/{MAX_RETRIES})...")
        _, decision = step01.run(client, draft_dir)
        if decision != "rejected":
            break
        if attempt < MAX_RETRIES:
            tg.send_text(f"Generating a fresh idea... (attempt {attempt + 1}/{MAX_RETRIES})")
        else:
            tg.send_text("All ideas rejected. Run --draft manually when ready.")

    print("=" * 60)
    if decision == "rejected":
        print("All ideas rejected via Telegram. Re-run --draft to try again.")
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
        dur_token = tg.new_token()
        tg.send_duration_prompt(dur_token)
        target_min = tg.wait_for_duration(dur_token)
        tg.send_text(f"Extending music to {target_min} min... (takes 3-5 min)")
        step02 = _load_step("02_extend.py")
        step02.run(draft_dir, target_min=target_min)
        tg.send_text("Music ready.")

    # Step 3 — Assemble video (skip if video.mp4 already exists and non-empty)
    video_path = os.path.join(draft_dir, "video.mp4")
    video_ok = os.path.exists(video_path) and os.path.getsize(video_path) > 0
    if video_ok:
        print(f"[orchestrator] video.mp4 already present — skipping assemble step.")
        tg.send_text("video.mp4 already exists — skipping assemble step.")
    elif os.path.exists(video_path):
        print(f"[orchestrator] video.mp4 is empty/corrupt — re-assembling.")
        tg.send_text("video.mp4 was empty/corrupt — re-assembling...")
        os.remove(video_path)
    if not video_ok:
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

    # Optional: schedule publish time
    schedule_token = tg.new_token()
    tg.send_schedule_prompt(schedule_token)
    publish_at = tg.wait_for_schedule(schedule_token)

    # Step 4 — Upload
    step04 = _load_step("04_upload.py")
    video_id = step04.run(brain, draft_dir, publish_at=publish_at)

    if publish_at:
        from datetime import datetime
        from studio.telegram import IST
        dt = datetime.fromisoformat(publish_at)
        schedule_label = f"Scheduled for {dt.strftime('%d %b %Y %I:%M %p')} IST"
    else:
        schedule_label = "Live now"

    upload_caption = (
        f"Uploaded! {schedule_label}\n\n"
        f"{brain.get('title', '')}\n\n"
        f"https://youtu.be/{video_id}"
    )
    if preview_image:
        tg.send_photo(preview_image, upload_caption)
    else:
        tg.send_text(upload_caption)
    print("=" * 60)
    print(f"DONE — https://youtu.be/{video_id}")
    print("=" * 60)


# ── Cleanup ───────────────────────────────────────────────────────────────────

def do_cleanup(days: int = 30):
    drafts_root = os.path.join(STUDIO_DIR, "drafts")
    if not os.path.isdir(drafts_root):
        print("[cleanup] No drafts folder found.")
        return
    cutoff = date.today() - timedelta(days=days)
    removed = []
    for name in sorted(os.listdir(drafts_root)):
        folder = os.path.join(drafts_root, name)
        if not os.path.isdir(folder):
            continue
        try:
            folder_date = date.fromisoformat(name)
        except ValueError:
            continue
        if folder_date < cutoff:
            shutil.rmtree(folder)
            removed.append(name)
    if removed:
        print(f"[cleanup] Removed {len(removed)} folder(s): {', '.join(removed)}")
    else:
        print(f"[cleanup] Nothing to remove (cutoff: {cutoff}).")


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
    elif "--cleanup" in sys.argv:
        days = 30
        for i, arg in enumerate(sys.argv):
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
        do_cleanup(days)
    else:
        print(__doc__)
        print("Error: pass --draft, --publish, or --cleanup")
        sys.exit(1)


if __name__ == "__main__":
    main()
