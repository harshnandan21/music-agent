"""
Music Agent Orchestrator
Pipeline: Brain → Music → Image → Assemble → Thumbnail → Upload
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


def main():
    print("=" * 60)
    print("MUSIC AGENT — Starting pipeline")
    print("=" * 60)

    clean_output()
    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        import importlib

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

        # Step 5 — Thumbnail (PIL)
        thumb_mod = importlib.import_module("06_thumbnail")
        thumbnail = thumb_mod.run(brain, image_path)

        # Step 6 — Upload (YouTube)
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
