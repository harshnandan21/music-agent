"""
One-shot upload script for already-generated output files.
Creates the YouTube playlist on first run and saves the ID to .env.
"""
import sys, os, importlib.util
sys.path.insert(0, os.path.dirname(__file__))

from config import OUTPUT_DIR
from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_FILE)

# ── Load upload module ────────────────────────────────────────────────────────
spec = importlib.util.spec_from_file_location(
    "upload", os.path.join(os.path.dirname(__file__), "steps", "07_upload.py")
)
upload_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_mod)

# ── Brain data for this video ─────────────────────────────────────────────────
brain = {
    "title": "Unwind After Work? Sitar & Raga Yaman Kalyan for Serenity | Dusk Relaxation",
    "description": (
        "Drifting into the serene embrace of dusk after a long day? "
        "Discover tranquility with this exquisite performance of Raga Yaman Kalyan on the sitar. "
        "Known for its deeply romantic and gentle character, Yaman Kalyan is the perfect companion "
        "to unwind and find peace as the day fades into night. This ancient Indian classical melody "
        "will transport you to a state of calm, melting away the stress and fatigue of work. "
        "Let the delicate ornamentation and soothing harmonies wash over you.\n\n"
        "Ideal for meditation, gentle yoga, or simply enjoying a moment of reflective stillness.\n\n"
        "#RagaYamanKalyan #SitarMusic #IndianClassicalMusic #RelaxationMusic #DuskMusic "
        "#AfterWorkRelax #MeditationMusic #ClassicalIndian #StressRelief #SereneSounds "
        "#DhunDetox #RagaMusic #IndianMusic #Sitar #ClassicalMusic"
    ),
    "tags": [
        "Raga Yaman Kalyan", "Sitar Music", "Indian Classical Music",
        "Relaxation Music", "Dusk Music", "After Work Relaxation",
        "Meditation Music", "Stress Relief", "Calming Music",
        "Traditional Indian Music", "Raga Music", "DhunDetox",
        "Indian Music", "Sitar", "Classical Music", "Sleep Music",
        "Ambient Music", "Focus Music", "Healing Music", "Yoga Music",
    ],
}


def _get_or_create_playlist(youtube):
    """Return existing playlist ID from .env or create a new one."""
    playlist_id = os.environ.get("YOUTUBE_PLAYLIST_ID", "")
    if playlist_id:
        print(f"[upload] Using playlist: {playlist_id}")
        return playlist_id

    print("[upload] Creating YouTube playlist 'DhunDetox — Indian Classical Music'...")
    res = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "DhunDetox — Indian Classical Music",
                "description": (
                    "A curated collection of Indian classical music for relaxation, "
                    "meditation, focus, and sleep. Ragas played on sitar, bansuri flute, "
                    "santoor, sarod, and veena."
                ),
                "defaultLanguage": "en",
            },
            "status": {"privacyStatus": "public"},
        },
    ).execute()

    playlist_id = res["id"]
    set_key(ENV_FILE, "YOUTUBE_PLAYLIST_ID", playlist_id)
    print(f"[upload] Playlist created: https://youtube.com/playlist?list={playlist_id}")
    return playlist_id


# ── Auth + build YouTube client ───────────────────────────────────────────────
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

creds = upload_mod._get_credentials()
youtube = build("youtube", "v3", credentials=creds)

playlist_id = _get_or_create_playlist(youtube)

# ── Upload video ──────────────────────────────────────────────────────────────
body = {
    "snippet": {
        "title":           brain["title"],
        "description":     brain["description"],
        "tags":            brain["tags"],
        "categoryId":      "10",   # Music
        "defaultLanguage": "en",
    },
    "status": {
        "privacyStatus":           "public",
        "selfDeclaredMadeForKids": False,
    },
}

video_path     = os.path.join(OUTPUT_DIR, "final_video.mp4")
thumbnail_path = os.path.join(OUTPUT_DIR, "thumbnail.jpg")

media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=5 * 1024 * 1024)
print(f"[upload] Uploading: {brain['title']}")

request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"[upload] {int(status.progress() * 100)}% uploaded...")

video_id = response["id"]
print(f"[upload] Uploaded: https://youtu.be/{video_id}")

# ── Set thumbnail ─────────────────────────────────────────────────────────────
youtube.thumbnails().set(
    videoId=video_id,
    media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
).execute()
print("[upload] Thumbnail set.")

# ── Add to playlist ───────────────────────────────────────────────────────────
youtube.playlistItems().insert(
    part="snippet",
    body={
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id},
        }
    },
).execute()
print(f"[upload] Added to playlist: https://youtube.com/playlist?list={playlist_id}")

print(f"\nDone!  https://youtu.be/{video_id}")
