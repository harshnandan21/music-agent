"""
Studio Orchestrator — unified manual + auto workflow

Phase 1 (--draft):
  Runs the brain (Gemini) → saves idea to studio/drafts/YYYY-MM-DD/brain.json
  → sends Telegram: APPROVE / REJECT
  → if approved → Telegram: AUTO or MANUAL?

  AUTO  → asks duration → generates Lyria music + Gemini image → assembles video
          → Telegram: APPROVE / REJECT upload + schedule → uploads
  MANUAL → sends drop-files instructions → exits
           (run --publish when files are ready)

Phase 2 (--publish)  [MANUAL mode, or AUTO resume after interruption]:
  Reads the draft folder → extends music clips → assembles video
  → sends Telegram preview → uploads on approval.

Usage:
  python studio/orchestrator.py --draft
  python studio/orchestrator.py --publish
  python studio/orchestrator.py --publish --date 2026-05-25
  python studio/orchestrator.py --publish --no-telegram
  python studio/orchestrator.py --publish --shorts   ← enable Shorts (disabled by default)

Shorts strategy: Shorts are disabled by default until 1,000 organic subscribers.
  Evidence: every top channel in this niche (Raga Heal 60K, Soulful Breathscape 11K)
  posts zero Shorts — healing music is a search/recommendation niche, not a scroll
  niche. Shorts dilute watch-time quality signals. Re-enable with --shorts after 1K subs.

Before running --publish in MANUAL mode, drop into studio/drafts/YYYY-MM-DD/:
  clip_1.mp3 / .wav   (required) your music
  clip_2.mp3 / .wav   (optional) second clip — crossfaded with clip_1
  clip_1.mp4          (recommended) Veo 8-sec loop, variant 1 (e.g. flame)
  clip_2.mp4          (recommended) Veo 8-sec loop, variant 2 (e.g. smoke)
  clip_3.mp4          (recommended) Veo 8-sec loop, variant 3 (e.g. sky glow)
  clip_4.mp4          (optional)    Veo 8-sec loop, variant 4 (e.g. ripple)
  clip.mp4            (fallback if no clip_N.mp4) single Veo loop
  background.png      (fallback if no .mp4 clips) static image
  thumbnail.png       (required) custom thumbnail
"""

import importlib.util, io, json, os, shutil, sys, traceback
from datetime import date, timedelta

# Ensure stdout handles emoji/Unicode on Windows without crashing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STUDIO_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
STEPS_DIR  = os.path.join(STUDIO_DIR, "steps")

sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, STUDIO_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Force line-buffered stdout so progress shows in real-time when piped to a file
sys.stdout.reconfigure(line_buffering=True)

from google import genai
from config import GEMINI_API_KEY
from studio.utils import get_duration
import studio.telegram as tg

NO_TELEGRAM    = "--no-telegram" in sys.argv
SHORTS_ENABLED = "--shorts" in sys.argv
TEST_MODE      = "--test" in sys.argv
ASSEMBLE_ONLY  = "--assemble-only" in sys.argv


def _next_upload_slot() -> str:
    """Next 00:00 UTC (5:30 AM IST) at least 5 min from now — YouTube scheduling requirement."""
    from datetime import datetime, timezone, timedelta
    now  = datetime.now(timezone.utc)
    slot = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if slot <= now + timedelta(minutes=5):
        slot += timedelta(days=1)
    return slot.isoformat()


def _tg_send(text: str):
    if not NO_TELEGRAM:
        tg.send_text(text)
    else:
        print(f"[telegram-skip] {text}")


def _load_step(filename: str):
    """Load a studio/steps/ module by filename (handles digit-prefixed names)."""
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


def _save_brain(brain: dict, draft_dir: str):
    brain_path = os.path.join(draft_dir, "brain.json")
    with open(brain_path, "w", encoding="utf-8") as f:
        json.dump(brain, f, indent=2, ensure_ascii=False)


# ── Manual prompts helper ─────────────────────────────────────────────────────

def _send_manual_prompts(brain: dict, date_str: str, file_mode: str = "LAPTOP"):
    """Output Suno + Gemini prompts — to terminal if LAPTOP, to Telegram if TELEGRAM.
    Reuses 01_draft.py's prompt builders so quality matches the draft .txt file."""
    draft_step = _load_step("01_draft.py")
    suno_text  = draft_step._suno_prompt(brain)
    bg_text    = draft_step._gemini_bg_prompt(brain)

    use_tg = (file_mode.upper() == "TELEGRAM")

    def _out(plain: str, html: str = ""):
        if use_tg:
            tg.send_text(html or plain)
        else:
            print(plain)

    # ── 1. SUNO custom mode ───────────────────────────────────────────────────
    _out(
        f"\n{'='*60}\n{suno_text}\n",
        f"<b>🎵 SUNO — Custom Mode</b>\n\n<code>{suno_text}</code>",
    )

    # ── 2. Gemini background image ────────────────────────────────────────────
    _out(
        f"\n{'='*60}\n{bg_text}\n",
        f"<b>🖼️ Gemini — Background Image</b>\n\n<code>{bg_text}</code>",
    )

    drop_plain = (
        f"\n{'='*60}\n📂 Drop files into: studio/drafts/{date_str}/\n{'='*60}\n"
        f"  clip_1.mp3 or .wav  (required — music)\n"
        f"  clip_2.mp3 or .wav  (optional — second music clip)\n"
        f"  clip_1.mp4          (recommended — Veo clip, flame motion)\n"
        f"  clip_2.mp4          (recommended — Veo clip, smoke motion)\n"
        f"  clip_3.mp4          (recommended — Veo clip, sky glow)\n"
        f"  clip_4.mp4          (optional   — Veo clip, water ripple)\n"
        f"  background.png      (required if no .mp4 clips — static fallback)\n"
        f"  thumbnail.png       (required)\n\n"
        f"Then run:\n"
        f"  python studio/orchestrator.py --publish --date {date_str}\n"
    )
    drop_html = (
        f"<b>📂 Drop files into:</b>\n"
        f"<code>studio/drafts/{date_str}/</code>\n\n"
        f"  clip_1.mp3 or .wav  (required — music)\n"
        f"  clip_2.mp3 or .wav  (optional — second music clip)\n"
        f"  clip_1.mp4          (recommended — Veo: flame motion)\n"
        f"  clip_2.mp4          (recommended — Veo: smoke motion)\n"
        f"  clip_3.mp4          (recommended — Veo: sky glow)\n"
        f"  clip_4.mp4          (optional   — Veo: water ripple)\n"
        f"  background.png      (fallback if no .mp4 clips)\n"
        f"  thumbnail.png       (required)\n\n"
        f"Then run:\n"
        f"<code>python studio/orchestrator.py --publish --date {date_str}</code>"
    )
    _out(drop_plain, drop_html)


# ── Short helper ─────────────────────────────────────────────────────────────

def _do_short(brain: dict, draft_dir: str):
    """Generate short.mp4 and upload it as a YouTube Short. Non-fatal on failure.
    Disabled by default — pass --shorts to enable. Strategy: no Shorts until 1K organic subs."""
    if not SHORTS_ENABLED:
        print("[orchestrator] Shorts skipped (pass --shorts to enable — wait until 1K organic subs)")
        return
    try:
        _tg_send("Generating 60-sec Short (scheduled 11 PM)...")
        step05   = _load_step("05_short.py")
        step05.run(brain, draft_dir)
        step04   = _load_step("04_upload.py")
        short_id = step04.run_short(brain, draft_dir)
        if short_id:
            _tg_send(f"Short uploaded: https://youtu.be/{short_id}")
        # Post to Instagram + Facebook Page
        try:
            step08  = _load_step("08_social.py")
            results = step08.run(brain, draft_dir)
            ig_id   = results.get("instagram")
            fb_id   = results.get("facebook")
            msg     = "Social posted:"
            if ig_id:
                msg += f"\n📸 Instagram: https://www.instagram.com/reel/{ig_id}/"
            if fb_id:
                msg += f"\n📘 Facebook: posted (ID {fb_id})"
            if ig_id or fb_id:
                _tg_send(msg)
        except Exception as se:
            print(f"[orchestrator] Social posting failed (non-fatal): {se}")
    except Exception as e:
        print(f"[orchestrator] Short failed (non-fatal): {e}")
        _tg_send(f"Short skipped — {e}")


# ── AUTO pipeline ─────────────────────────────────────────────────────────────

def _do_auto_steps(client, brain: dict, draft_dir: str, target_min: int):
    """Full AUTO pipeline: Lyria music → Gemini image → assemble → upload."""
    date_str = os.path.basename(draft_dir)

    # Step A — Generate Lyria clips (saved as clip_1.mp3 … clip_4.mp3)
    music_path = os.path.join(draft_dir, "music.flac")
    if not os.path.exists(music_path):
        _tg_send(f"Generating music via Lyria (~15 min for 4 clips)...")
        auto_music = _load_step("auto_music.py")
        auto_music.run(client, brain, draft_dir)

        # Step B — Extend / loop clips to target duration
        _tg_send(f"Extending to {target_min} min...")
        step02 = _load_step("02_extend.py")
        step02.run(draft_dir, target_min=target_min)
        _tg_send("Music ready.")
    else:
        print("[orchestrator] music.flac already present — skipping music generation.")

    # Step C — Generate background image
    image_path = os.path.join(draft_dir, "background.png")
    if not os.path.exists(image_path):
        _tg_send("Generating background image via Gemini...")
        auto_image = _load_step("auto_image.py")
        auto_image.run(client, brain, draft_dir)
        _tg_send("Image generated.")
    else:
        print("[orchestrator] background.png already present — skipping image generation.")

    # Step D — Assemble video
    video_path = os.path.join(draft_dir, "video.mp4")
    video_ok   = os.path.exists(video_path) and os.path.getsize(video_path) > 0
    if not video_ok:
        if os.path.exists(video_path):
            os.remove(video_path)
        _tg_send("Assembling video (2-5 min)...")
        step03 = _load_step("03_assemble.py")
        step03.run(brain, draft_dir)
        _tg_send("Video assembled!")
    else:
        print("[orchestrator] video.mp4 already present — skipping assemble.")

    # Step E — Upload approval + schedule
    preview_image = next(
        (os.path.join(draft_dir, n)
         for n in ["background.png", "background.jpg", "thumbnail.png"]
         if os.path.exists(os.path.join(draft_dir, n))),
        None,
    )

    if NO_TELEGRAM:
        publish_at = _next_upload_slot()
        from datetime import datetime, timezone
        _dt = datetime.fromisoformat(publish_at)
        print(f"[orchestrator] --no-telegram: scheduling for {_dt.strftime('%d %b %Y %H:%M UTC')} (5:30 AM IST)")
        decision   = "approved"
    else:
        token = tg.new_token()
        caption = (
            f"AUTO complete — ready to upload?\n\n"
            f"Raga: {brain.get('raga', '—')}\n"
            f"Instruments: {brain.get('instrument', '—')}\n\n"
            f"Title:\n{brain.get('title', '—')}"
        )
        tg.send_approval(preview_image, caption, token)
        decision = tg.wait_for_decision(token, timeout_seconds=21600)

        if decision == "rejected":
            _tg_send(f"Upload skipped. Files are in studio/drafts/{date_str}/")
            return

        sch_token = tg.new_token()
        tg.send_schedule_prompt(sch_token)
        publish_at = tg.wait_for_schedule(sch_token)

    step04   = _load_step("04_upload.py")
    video_id = step04.run(brain, draft_dir, publish_at=publish_at)

    brain["main_video_id"] = video_id
    _save_brain(brain, draft_dir)

    if publish_at:
        from datetime import datetime
        dt    = datetime.fromisoformat(publish_at)
        label = f"Scheduled for {dt.strftime('%d %b %Y %I:%M %p')} IST"
    else:
        label = "Live now"

    upload_msg = f"Uploaded! {label}\n\nhttps://youtu.be/{video_id}"
    _tg_send(upload_msg)
    print(f"\nDONE — https://youtu.be/{video_id}")

    _do_short(brain, draft_dir)


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
    _, _ = step01.run(client, draft_dir)

    brain = _load_brain(draft_dir)
    brain["mode"] = "manual"
    _save_brain(brain, draft_dir)

    print("=" * 60)
    print(f"Draft saved: {draft_dir}")
    print("=" * 60)


# ── Phase 2 ───────────────────────────────────────────────────────────────────

def do_publish(date_str: str):
    print("=" * 60)
    print(f"STUDIO — Publish  ({date_str})")
    print("=" * 60)

    draft_dir = _draft_dir(date_str)
    brain     = _load_brain(draft_dir)
    print("[orchestrator] Title:", brain.get("title", ""))
    _tg_send(f"Publish started for {date_str}\n{brain.get('title', '')}")

    # ── MANUAL flow ───────────────────────────────────────────────────────────

    # Extend music (skip if music.flac already exists)
    music_path = os.path.join(draft_dir, "music.flac")
    if os.path.exists(music_path):
        print("[orchestrator] music.flac already present — skipping extend step.")
        _tg_send("music.flac already exists — skipping extend step.")
    else:
        if TEST_MODE:
            target_min = 1
            print(f"[orchestrator] --test: capping at {target_min} min")
        else:
            target_min = 60
            print(f"[orchestrator] Defaulting to {target_min} min")
        _tg_send(f"Extending music to {target_min} min... (takes 3-5 min)")
        step02 = _load_step("02_extend.py")
        step02.run(draft_dir, target_min=target_min)
        _tg_send("Music ready.")

    # Assemble video (skip if video.mp4 already exists and readable)
    video_path = os.path.join(draft_dir, "video.mp4")
    try:
        video_ok = os.path.exists(video_path) and get_duration(video_path) > 60
    except Exception:
        video_ok = False
    if video_ok:
        print("[orchestrator] video.mp4 already present — skipping assemble step.")
        _tg_send("video.mp4 already exists — skipping assemble step.")
    else:
        if os.path.exists(video_path):
            print("[orchestrator] video.mp4 is empty/corrupt — re-assembling.")
            _tg_send("video.mp4 was empty/corrupt — re-assembling...")
            os.remove(video_path)
        _tg_send("Assembling video (clip + music)... (takes 2-4 min)")
        step03 = _load_step("03_assemble.py")
        step03.run(brain, draft_dir)
        _tg_send("Video assembled.")

    if ASSEMBLE_ONLY:
        print("[orchestrator] --assemble-only: stopping after assembly. Check video.mp4 in draft folder.")
        return

    # Thumbnail — use manually dropped thumbnail.png (Gemini-generated).
    # Pass --generate-thumbnail to auto-generate a PIL placeholder instead.
    thumb_path = os.path.join(draft_dir, "thumbnail.png")
    if not os.path.exists(thumb_path) and "--generate-thumbnail" in sys.argv:
        try:
            step06 = _load_step("06_thumbnail.py")
            step06.run(brain, draft_dir)
        except Exception as e:
            print(f"[orchestrator] Thumbnail generation failed (non-fatal): {e}")
    elif not os.path.exists(thumb_path):
        print("[orchestrator] No thumbnail.png found — drop your Gemini thumbnail into the draft folder before uploading.")

    # Approval — show thumbnail as preview image
    preview_image = next(
        (os.path.join(draft_dir, n)
         for n in ["thumbnail.png", "thumbnail.jpg", "background_watermarked.png", "background.png"]
         if os.path.exists(os.path.join(draft_dir, n))),
        None,
    )

    # Always schedule for next 00:00 UTC (5:30 AM IST)
    publish_at = _next_upload_slot()
    from datetime import datetime, timezone
    _dt = datetime.fromisoformat(publish_at)
    slot_label = _dt.strftime('%d %b %Y %H:%M UTC') + ' (5:30 AM IST)'
    print(f"[orchestrator] Scheduling for {slot_label}")

    if not NO_TELEGRAM:
        token = tg.new_token()
        caption = (
            f"Ready to upload?\n\n"
            f"Raga: {brain.get('raga', '—')}\n"
            f"Instruments: {brain.get('instrument', '—')}\n\n"
            f"Title:\n{brain.get('title', '—')}\n\n"
            f"Hook: {brain.get('thumbnail_hook', '—')}\n"
            f"Tagline: {brain.get('thumbnail_tagline', '—')}\n\n"
            f"Scheduled for: {slot_label}"
        )
        tg.send_approval(preview_image, caption, token)
        decision = tg.wait_for_decision(token, timeout_seconds=21600)

        if decision == "rejected":
            print("[orchestrator] Upload rejected via Telegram. Files kept in draft folder.")
            sys.exit(0)

    file_mb = os.path.getsize(os.path.join(draft_dir, "video.mp4")) / 1_048_576
    _tg_send(f"⬆️ Uploading now ({file_mb:.0f} MB)... will notify at 25/50/75% and when done.")

    step04   = _load_step("04_upload.py")
    video_id = step04.run(brain, draft_dir, publish_at=publish_at)

    brain["main_video_id"] = video_id
    _save_brain(brain, draft_dir)

    if publish_at:
        from datetime import datetime
        dt    = datetime.fromisoformat(publish_at)
        label = f"Scheduled for {dt.strftime('%d %b %Y %I:%M %p')} IST"
    else:
        label = "Live now"

    upload_caption = f"Uploaded! {label}\n\n{brain.get('title', '')}\n\nhttps://youtu.be/{video_id}"
    _tg_send(upload_caption)
    print(f"\nDONE — https://youtu.be/{video_id}")

    _do_short(brain, draft_dir)
    _cleanup_draft(draft_dir)
    print("=" * 60)


# ── Cleanup ───────────────────────────────────────────────────────────────────

# video.mp4 kept 5 days post-upload (re-upload safety net), then auto-deleted
_VIDEO_KEEP_DAYS = 5
_LARGE_FILE_DAYS = 5
_LARGE_FILES     = {"video.mp4", "music.flac", "music.mp3", "short.mp4"}
# Entire draft folder removed after this many days
_FOLDER_DAYS     = 30

# Files always safe to keep (never touched by immediate cleanup)
_KEEP_NAMES = {"brain.json", "background.png", "background.jpg", "background.jpeg",
               "thumbnail.png", "thumbnail.jpg", "video.mp4", "short.mp4", "music.flac"}
_KEEP_PREFIXES = ("clip_", "clip.")
_KEEP_SUFFIXES = (".wav", ".mp3")


def _cleanup_draft(draft_dir: str):
    """After upload: delete intermediate files, ask via Telegram before removing."""
    to_delete = []
    for fname in os.listdir(draft_dir):
        fpath = os.path.join(draft_dir, fname)
        if not os.path.isfile(fpath):
            continue
        if fname in _KEEP_NAMES:
            continue
        if any(fname.startswith(p) for p in _KEEP_PREFIXES):
            continue
        if any(fname.endswith(s) for s in _KEEP_SUFFIXES):
            continue
        to_delete.append((fname, fpath))

    if not to_delete:
        print("[cleanup] No intermediate files to remove.")
        return

    total_mb = sum(os.path.getsize(p) / 1_048_576 for _, p in to_delete)
    file_list = "\n".join(f"  • {n} ({os.path.getsize(p)/1_048_576:.1f} MB)" for n, p in to_delete)
    msg = (
        f"🗑 Clean up intermediate files? ({total_mb:.0f} MB total)\n\n"
        f"{file_list}\n\n"
        f"video.mp4 is kept for {_VIDEO_KEEP_DAYS} days then auto-deleted."
    )

    if NO_TELEGRAM:
        for fname, fpath in to_delete:
            size_mb = os.path.getsize(fpath) / 1_048_576
            os.remove(fpath)
            print(f"[cleanup] Deleted {fname} ({size_mb:.1f} MB)")
        print(f"[cleanup] Freed {total_mb:.0f} MB of intermediate files.")
        return

    token = tg.new_token()
    tg.send_choice_prompt(token, msg, [("🗑 Clean Up", "CLEANUP"), ("⏭ Skip", "SKIP")])
    choice = tg.wait_for_choice(token, timeout_seconds=600)  # 10 min — don't block pipeline
    if choice == "CLEANUP":
        for fname, fpath in to_delete:
            size_mb = os.path.getsize(fpath) / 1_048_576
            os.remove(fpath)
            print(f"[cleanup] Deleted {fname} ({size_mb:.1f} MB)")
        _tg_send(f"✅ Cleaned up {total_mb:.0f} MB of intermediate files.\nvideo.mp4 kept for {_VIDEO_KEEP_DAYS} days.")
    else:
        print("[cleanup] Cleanup skipped by user.")


def _auto_cleanup():
    """Called automatically at startup: purge large files >5 days old, folders >30 days old."""
    drafts_root = os.path.join(STUDIO_DIR, "drafts")
    if not os.path.isdir(drafts_root):
        return
    today = date.today()
    for name in sorted(os.listdir(drafts_root)):
        folder = os.path.join(drafts_root, name)
        if not os.path.isdir(folder):
            continue
        try:
            folder_date = date.fromisoformat(name)
        except ValueError:
            continue
        age = (today - folder_date).days
        if age >= _FOLDER_DAYS:
            shutil.rmtree(folder)
            print(f"[cleanup] Removed old draft folder: {name}")
        elif age >= _LARGE_FILE_DAYS:
            for fname in _LARGE_FILES:
                fpath = os.path.join(folder, fname)
                if os.path.exists(fpath):
                    size_mb = os.path.getsize(fpath) / 1_048_576
                    os.remove(fpath)
                    print(f"[cleanup] Deleted {fname} from {name} ({size_mb:.0f} MB freed)")


def do_cleanup(days: int = _FOLDER_DAYS):
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
    _auto_cleanup()
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
