"""
Step 7 — YouTube Upload
Uploads the final video + thumbnail to YouTube via Data API v3.
Uses OAuth 2.0 (token file persisted across runs).
"""

import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import YOUTUBE_CLIENT_SECRET_FILE, YOUTUBE_TOKEN_FILE, get_playlist_id

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # required for comments
]


def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if os.path.exists(YOUTUBE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(YOUTUBE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def run(brain: dict, video_path: str, thumbnail_path: str, publish_at: str = None) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    # Build tags: start with curated tags[] (priority), then fill remaining
    # budget from keywords string. YouTube limits: 500 chars total (tags with
    # spaces count +2), max 30 chars per individual tag.
    def _yt_tag_len(tag):
        return len(tag) + (2 if " " in tag else 0)

    BUDGET = 470

    seen = set()
    candidates = []
    # 1. Curated tags[] first
    for t in brain.get("tags", []):
        t = t.strip()
        if t and t.isascii() and t not in seen:
            candidates.append(t)
            seen.add(t)
    # 2. Keywords string fills the rest
    for t in brain.get("keywords", "").split(","):
        t = t.strip()
        if t and t.isascii() and t not in seen:
            candidates.append(t)
            seen.add(t)

    safe_tags, total = [], 0
    for tag in candidates:
        cost = _yt_tag_len(tag)
        if total + cost > BUDGET:
            break
        safe_tags.append(tag)
        total += cost

    import re
    desc = brain.get("description", "")
    # Strip markdown bold/italic markers and blockquote symbols
    desc = re.sub(r'\*+', '', desc)
    desc = re.sub(r'^---$', '────────────────────────────', desc, flags=re.MULTILINE)
    clean_desc = re.sub(r'[<>]', '', desc)

    body = {
        "snippet": {
            "title":       brain.get("title", ""),
            "description": clean_desc,
            "tags":        safe_tags,
            "categoryId":  "10",  # Music
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "private" if publish_at else "public",
            "publishAt":     publish_at,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=5 * 1024 * 1024)
    print("[upload] Uploading:", brain['title'].encode('ascii', 'replace').decode('ascii'))

    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    response = None
    import time
    while response is None:
        try:
            status, response = request.next_chunk()
        except Exception as e:
            wait = 30
            print(f"[upload] Network error ({e}) — retrying in {wait}s...")
            time.sleep(wait)
            continue
        if status:
            pct = int(status.progress() * 100)
            print(f"[upload] {pct}% uploaded...")

    video_id = response["id"]
    print(f"[upload] Uploaded: https://youtu.be/{video_id}")

    # Set thumbnail (optional — skipped if no path provided)
    if thumbnail_path:
        try:
            # Compress to under 2MB (YouTube limit) before uploading
            import io
            from PIL import Image
            img = Image.open(thumbnail_path).convert("RGB")
            for quality in (85, 70, 55, 40):
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality)
                if buf.tell() < 2 * 1024 * 1024:
                    break
            buf.seek(0)
            import tempfile, pathlib
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(buf.read()); tmp.close()
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(tmp.name, mimetype="image/jpeg"),
            ).execute()
            pathlib.Path(tmp.name).unlink(missing_ok=True)
            print("[upload] Thumbnail set.")
        except Exception as e:
            print(f"[upload] Thumbnail skipped (verify channel at youtube.com/verify): {e}")
    else:
        print("[upload] No thumbnail — skipping.")

    # Add to the video's designated playlist (looked up by key from brain)
    playlist_id = get_playlist_id(brain.get("playlist", ""))
    if playlist_id:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
        print(f"[upload] Added to playlist '{brain.get('playlist')}' ({playlist_id})")
    else:
        print(f"[upload] No playlist ID set for key '{brain.get('playlist', 'none')}' — skipping.")

    return video_id


if __name__ == "__main__":
    print("Run orchestrator.py to trigger a full upload.")
