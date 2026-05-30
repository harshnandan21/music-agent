"""Automated pipeline runner for a locked-in studio idea.

Given a `brain` dict and a `draft_dir`, this will:
 - Generate music (02_music)
 - Generate background image (03_image)
 - Assemble video (05_assemble)
 - Create thumbnail (06_thumbnail)
 - Copy outputs into `draft_dir` as expected by the studio publish flow
 - Upload using the studio upload wrapper (04_upload)

This reuses the root-level `steps/` modules and copies their outputs into the studio draft folder.
"""

import importlib.util, os, shutil, sys, traceback

STUDIO_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)

from google import genai
from config import GEMINI_API_KEY, OUTPUT_DIR


def _load_step_by_path(path: str):
    spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(brain: dict, draft_dir: str) -> None:
    os.makedirs(draft_dir, exist_ok=True)

    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        # Music
        music_mod = _load_step_by_path(os.path.join(ROOT_DIR, "steps", "02_music.py"))
        music_path = music_mod.run(client, brain)
        dest_music = os.path.join(draft_dir, "music.mp3")
        shutil.copy(music_path, dest_music)
        print(f"[auto_publish] Music copied to {dest_music}")

        # Image
        image_mod = _load_step_by_path(os.path.join(ROOT_DIR, "steps", "03_image.py"))
        image_path = image_mod.run(client, brain)
        dest_bg = os.path.join(draft_dir, "background.png")
        shutil.copy(image_path, dest_bg)
        print(f"[auto_publish] Image copied to {dest_bg}")

        # Assemble
        assemble_mod = _load_step_by_path(os.path.join(ROOT_DIR, "steps", "05_assemble.py"))
        video_path = assemble_mod.run(brain, image_path, music_path)
        dest_vid = os.path.join(draft_dir, "video.mp4")
        shutil.copy(video_path, dest_vid)
        print(f"[auto_publish] Video copied to {dest_vid}")

        # Thumbnail
        thumb_mod = _load_step_by_path(os.path.join(ROOT_DIR, "steps", "06_thumbnail.py"))
        thumb_path = thumb_mod.run(brain, image_path)
        # Keep original filename (06_thumbnail produces thumbnail.jpg)
        dest_thumb = os.path.join(draft_dir, os.path.basename(thumb_path))
        shutil.copy(thumb_path, dest_thumb)
        print(f"[auto_publish] Thumbnail copied to {dest_thumb}")

        # Upload using studio's thin wrapper (04_upload.py)
        upload_mod = _load_step_by_path(os.path.join(STUDIO_DIR, "steps", "04_upload.py"))
        video_id = upload_mod.run(brain, draft_dir, publish_at=None)
        brain["main_video_id"] = video_id

        print(f"[auto_publish] Uploaded: https://youtu.be/{video_id}")

        # Generate + upload Short (non-fatal)
        try:
            short_mod = _load_step_by_path(os.path.join(STUDIO_DIR, "steps", "05_short.py"))
            short_mod.run(brain, draft_dir)
            upload_mod.run_short(brain, draft_dir)
        except Exception as short_e:
            print(f"[auto_publish] Short failed (non-fatal): {short_e}")

    except Exception as e:
        print(f"[auto_publish] Error during automation: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("Run from studio/steps/01_draft.py after approval.")
