"""
Music Agent Orchestrator
Pipeline: Brain → Music → Image → Assemble → Thumbnail → [Approval] → Upload
"""

import os, sys, shutil, traceback
from google import genai
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "steps"))

from config import GEMINI_API_KEY, OUTPUT_DIR


def clean_output():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _await_approval(brain: dict, video_path: str, thumb_path: str) -> bool:
    """Print a review summary and wait for y/n. Returns True to proceed with upload."""
    print()
    print("=" * 60)
    print("  CONTENT READY — REVIEW BEFORE UPLOADING")
    print("=" * 60)
    print(f"  Title       : {brain.get('title', '')}")
    print(f"  Raga        : {brain.get('raga', '')}")
    print(f"  Instruments : {brain.get('instrument', '')}")
    print(f"  Use case    : {brain.get('use_case', '')}")
    print(f"  Hook angle  : {brain.get('hook_angle', '')}")
    print()
    print(f"  Video       : {video_path}")
    print(f"  Thumbnail   : {thumb_path}")
    print()
    print("  Open the files above to review, then answer below.")
    print("=" * 60)

    # Auto-approve when stdin is piped (non-interactive run like: echo y | python orchestrator.py)
    if not sys.stdin.isatty():
        try:
            answer = input("  Upload to YouTube? [y/n]: ").strip().lower()
        except EOFError:
            answer = "y"
        print(answer)
        return answer != "n"

    while True:
        answer = input("  Upload to YouTube? [y/n]: ").strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            print()
            print("  Upload cancelled. Files saved in output/ — run upload_only.py when ready.")
            return False
        print("  Please enter y or n.")


def main():
    resume    = "--resume" in sys.argv
    no_upload = "--no-upload" in sys.argv

    mode = "Resuming from assemble" if resume else "Starting pipeline"
    if no_upload:
        mode += " (no thumbnail / no upload)"
    print("=" * 60)
    print(f"MUSIC AGENT — {mode}")
    print("=" * 60)

    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        import importlib, json

        if resume:
            # Load brain from saved used_ideas.json (last entry)
            ideas_file = os.path.join(os.path.dirname(OUTPUT_DIR), "used_ideas.json")
            with open(ideas_file) as f:
                brain = json.load(f)[-1]
            music_path = os.path.join(OUTPUT_DIR, "music.mp3")
            image_path = os.path.join(OUTPUT_DIR, "background.png")
            print(f"[resume] Using: {brain.get('title', '')}")

            # Generate image if missing
            if not os.path.exists(image_path):
                print("[resume] background.png missing — generating image...")
                image_mod = importlib.import_module("03_image")
                image_path = image_mod.run(client, brain)
        else:
            clean_output()

            # Step 1 — Brain
            brain_mod = importlib.import_module("01_brain")
            brain = brain_mod.run(client)

            # Step 2 — Music (Lyria)
            music_mod = importlib.import_module("02_music")
            music_path = music_mod.run(client, brain)

            # Step 3 — Image (Imagen)
            image_mod = importlib.import_module("03_image")
            image_path = image_mod.run(client, brain)

        # Step 4 — Assemble (FFmpeg: static image + audio)
        assemble_mod = importlib.import_module("05_assemble")
        final_video = assemble_mod.run(brain, image_path, music_path)

        if no_upload:
            print("=" * 60)
            print(f"DONE (no-upload mode) — review files:")
            print(f"  Video : {final_video}")
            print(f"  Music : {music_path}")
            print(f"  Image : {image_path}")
            print("=" * 60)
            return

        # Step 5 — Thumbnail (PIL)
        thumb_mod = importlib.import_module("06_thumbnail")
        thumbnail = thumb_mod.run(brain, image_path)

        # Step 6 — Approval gate
        if not _await_approval(brain, final_video, thumbnail):
            sys.exit(0)

        # Step 7 — Upload (YouTube)
        upload_mod = importlib.import_module("07_upload")
        video_id = upload_mod.run(brain, final_video, thumbnail)

        print("=" * 60)
        print(f"DONE — https://youtu.be/{video_id}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
