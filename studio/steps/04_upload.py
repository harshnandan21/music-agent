"""
Studio Step 4 — Upload
Uploads draft_dir/video.mp4 to YouTube using the brain.json metadata.
Optionally sets draft_dir/thumbnail.png as the video thumbnail.
Thin wrapper around the root-level steps/07_upload.py.
"""

import importlib.util, os, sys

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)


def _load_upload_mod():
    spec = importlib.util.spec_from_file_location(
        "upload", os.path.join(ROOT_DIR, "steps", "07_upload.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(brain: dict, draft_dir: str, publish_at: str = None) -> str:
    video_path = os.path.join(draft_dir, "video.mp4")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"[upload] video.mp4 not found in {draft_dir}")

    thumbnail_path = None
    for name in ["thumbnail.png", "thumbnail.jpg", "background.png", "background.jpg"]:
        p = os.path.join(draft_dir, name)
        if os.path.exists(p):
            thumbnail_path = p
            break

    upload_mod = _load_upload_mod()
    video_id = upload_mod.run(brain, video_path, thumbnail_path, publish_at=publish_at)
    return video_id
