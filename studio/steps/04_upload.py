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


def run_short(brain: dict, draft_dir: str) -> str | None:
    """Upload draft_dir/short.mp4 as a YouTube Short. Returns video_id or None if skipped."""
    short_path = os.path.join(draft_dir, "short.mp4")
    if not os.path.exists(short_path):
        print("[upload_short] short.mp4 not found — skipping.")
        return None

    raga      = brain.get("raga", "")
    instr     = brain.get("instrument", "")
    use_case  = brain.get("use_case", "").replace("_", " ").title()
    raga_tag  = raga.replace(" ", "")

    short_brain = dict(brain)
    short_brain["title"] = f"{raga} · {instr} | {use_case} #Shorts"[:100]
    main_id   = brain.get("main_video_id", "")
    full_link = f"https://youtu.be/{main_id}" if main_id else "https://youtube.com/@DhunDetox"
    short_brain["description"] = (
        f"30-second preview of today's full Indian classical music.\n\n"
        f"▶ Full version ({use_case.title()}): {full_link}\n\n"
        f"#{raga_tag} #IndianClassical #Meditation #Shorts #YouTubeShorts"
    )
    short_brain["tags"] = (brain.get("tags") or [])[:5] + ["Shorts", "YouTubeShorts"]
    short_brain["playlist"] = ""  # don't add Shorts to the long-form playlist

    upload_mod = _load_upload_mod()
    video_id = upload_mod.run(short_brain, short_path, thumbnail_path=None)
    print(f"[upload_short] Short live: https://youtu.be/{video_id}")
    return video_id
