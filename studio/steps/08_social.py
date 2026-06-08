"""
Studio Step 8 — Social
Posts the Short to Instagram Reels and Facebook Page.

Requirements in .env:
    INSTAGRAM_USER_ID          — numeric Instagram user ID
    INSTAGRAM_ACCESS_TOKEN     — long-lived user token (instagram_content_publish scope)
    FACEBOOK_PAGE_ID           — numeric Page ID
    FACEBOOK_PAGE_ACCESS_TOKEN — Page access token (pages_manage_posts scope)
"""

import os, sys, time, requests

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)

GRAPH_URL = "https://graph.facebook.com/v19.0"


def _get_env(key: str) -> str:
    val = os.environ.get(key, "")
    if not val:
        raise EnvironmentError(f"[social] Missing env var: {key}")
    return val


# ── Temp file hosting (Instagram requires a public URL for video) ─────────────

def _upload_to_host(file_path: str) -> str:
    """Upload file to 0x0.st and return public URL. Free, no account needed."""
    print("[social] Uploading short to temp host for Instagram...")
    with open(file_path, "rb") as f:
        resp = requests.post("https://0x0.st", files={"file": f}, timeout=180)
    resp.raise_for_status()
    url = resp.text.strip()
    print(f"[social] Hosted at: {url}")
    return url


# ── Caption builder ───────────────────────────────────────────────────────────

def _build_caption(brain: dict) -> str:
    tagline  = brain.get("thumbnail_tagline", "")
    title    = brain.get("title", "")
    raga     = brain.get("raga", "")
    raga_tag = raga.replace(" ", "")
    main_id  = brain.get("main_video_id", "")
    yt_link  = f"\n\n▶ Full 1-hour version on YouTube:\nhttps://youtu.be/{main_id}" if main_id else ""

    return (
        f"{tagline}\n\n"
        f"🎵 {title}{yt_link}\n\n"
        f"#{raga_tag} #IndianClassical #MeditationMusic #HealingMusic "
        f"#SoundHealing #Raga #DhunDetox #Reels"
    )


# ── Instagram Reels ───────────────────────────────────────────────────────────

def post_instagram_reel(brain: dict, short_path: str) -> str:
    """Publish short.mp4 as an Instagram Reel. Returns media ID."""
    user_id = _get_env("INSTAGRAM_USER_ID")
    token   = _get_env("INSTAGRAM_ACCESS_TOKEN")
    caption = _build_caption(brain)

    # 1 — Host the video so Instagram can fetch it
    video_url = _upload_to_host(short_path)

    # 2 — Create media container
    print("[social] Creating Instagram Reel container...")
    resp = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        data={
            "media_type":   "REELS",
            "video_url":    video_url,
            "caption":      caption,
            "access_token": token,
        },
        timeout=60,
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    print(f"[social] Container: {container_id}")

    # 3 — Poll until container is processed (max 5 min)
    print("[social] Waiting for Instagram to process video...")
    for attempt in range(20):
        time.sleep(15)
        st = requests.get(
            f"{GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        ).json().get("status_code", "")
        print(f"[social] IG status: {st} (attempt {attempt + 1}/20)")
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise RuntimeError("[social] Instagram container processing failed")
    else:
        raise RuntimeError("[social] Instagram timed out after 5 min")

    # 4 — Publish
    print("[social] Publishing Instagram Reel...")
    pub = requests.post(
        f"{GRAPH_URL}/{user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=60,
    )
    pub.raise_for_status()
    media_id = pub.json()["id"]
    print(f"[social] Instagram Reel live: https://www.instagram.com/reel/{media_id}/")
    return media_id


# ── Facebook Page Reel ────────────────────────────────────────────────────────

def post_facebook_reel(brain: dict, short_path: str) -> str:
    """Upload short.mp4 as a Facebook Page video/Reel. Returns video ID."""
    page_id = _get_env("FACEBOOK_PAGE_ID")
    token   = _get_env("FACEBOOK_PAGE_ACCESS_TOKEN")
    caption = _build_caption(brain)
    title   = brain.get("title", "")[:100]

    print("[social] Uploading Reel to Facebook Page...")
    with open(short_path, "rb") as f:
        resp = requests.post(
            f"{GRAPH_URL}/{page_id}/videos",
            data={
                "title":        title,
                "description":  caption,
                "access_token": token,
            },
            files={"source": f},
            timeout=300,
        )
    resp.raise_for_status()
    video_id = resp.json().get("id", "")
    print(f"[social] Facebook Reel posted: {video_id}")
    return video_id


# ── Entry point ───────────────────────────────────────────────────────────────

def run(brain: dict, draft_dir: str) -> dict:
    short_path = os.path.join(draft_dir, "short.mp4")
    if not os.path.exists(short_path):
        raise FileNotFoundError(f"[social] short.mp4 not found in {draft_dir}")

    results = {}

    # Instagram
    try:
        ig_id = post_instagram_reel(brain, short_path)
        results["instagram"] = ig_id
    except Exception as e:
        print(f"[social] Instagram failed (non-fatal): {e}")
        results["instagram"] = None

    # Facebook Page
    try:
        fb_id = post_facebook_reel(brain, short_path)
        results["facebook"] = fb_id
    except Exception as e:
        print(f"[social] Facebook failed (non-fatal): {e}")
        results["facebook"] = None

    return results
