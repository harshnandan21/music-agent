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
    SKIP = {"thumbnail.png", "thumbnail.jpg", "image_watermarked.png"}
    # Check fixed names first, then fall back to any PNG/JPG in the folder
    for name in ["thumbnail.png", "thumbnail.jpg", "background.png", "background.jpg"]:
        p = os.path.join(draft_dir, name)
        if os.path.exists(p):
            thumbnail_path = p
            break
    if not thumbnail_path:
        for f in sorted(os.listdir(draft_dir)):
            if f.lower().endswith((".png", ".jpg", ".jpeg")) and f not in SKIP:
                thumbnail_path = os.path.join(draft_dir, f)
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
    use_case  = brain.get("use_case", "").replace("_", " ")
    raga_tag  = raga.replace(" ", "")
    hook      = brain.get("thumbnail_hook", "").strip()
    tagline   = brain.get("thumbnail_tagline", "").strip()

    # Hook-driven title
    uc = use_case.lower()
    if any(w in uc for w in ("overthink", "overactive", "racing")):
        yt_title = f"Mind racing at midnight? Raga {raga} 396Hz #Shorts"
    elif any(w in uc for w in ("sleep", "insomnia")):
        yt_title = f"Cannot fall asleep? Raga {raga} for deep sleep #Shorts"
    elif any(w in uc for w in ("stress", "anxiety", "cortisol")):
        yt_title = f"Feeling overwhelmed? Raga {raga} for calm #Shorts"
    elif any(w in uc for w in ("morning", "prana", "reset", "energy")):
        yt_title = f"Need a morning reset? Raga {raga} #Shorts"
    elif any(w in uc for w in ("focus", "study", "clarity")):
        yt_title = f"Need to focus? Raga {raga} #Shorts"
    elif hook:
        yt_title = f"{hook} | Raga {raga} #Shorts"
    else:
        yt_title = f"Raga {raga} | 30 sec #Shorts"

    main_id   = brain.get("main_video_id", "")
    full_link = f"https://youtu.be/{main_id}" if main_id else ""
    full_line = f"\n\n▶ Full version: {full_link}" if full_link else ""

    # Hook-driven description
    if tagline:
        desc_hook = tagline
    elif hook:
        desc_hook = hook.title()
    else:
        desc_hook = use_case.title()

    short_brain = dict(brain)
    short_brain["title"] = yt_title[:100]
    short_brain["description"] = (
        f"{desc_hook}\n\n"
        f"30-second preview of the full Indian classical music experience.{full_line}\n\n"
        f"#{raga_tag} #IndianClassical #Meditation #Shorts #YouTubeShorts"
    )
    short_brain["tags"] = (brain.get("tags") or [])[:5] + ["Shorts", "YouTubeShorts"]
    short_brain["playlist"] = ""  # don't add Shorts to the long-form playlist

    upload_mod = _load_upload_mod()
    video_id = upload_mod.run(short_brain, short_path, thumbnail_path=None)
    print(f"[upload_short] Short live: https://youtu.be/{video_id}")

    # Post comment with the full-video link
    # Note: description links not tappable on mobile for newer channels;
    # comments are tappable. Pin via YouTube Studio for max visibility.
    if full_link:
        try:
            from googleapiclient.discovery import build
            creds = upload_mod._get_credentials()
            yt = build("youtube", "v3", credentials=creds)
            yt.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": (
                                    f"▶ Full version ({use_case.title()}):\n{full_link}\n\n"
                                    f"Subscribe for daily Indian classical music 🎵"
                                )
                            }
                        }
                    }
                }
            ).execute()
            print(f"[upload_short] Comment posted with full video link.")
        except Exception as e:
            print(f"[upload_short] Comment post failed (non-fatal): {e}")

    return video_id
