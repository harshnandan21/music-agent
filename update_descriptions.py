"""
One-time script: append copyright line to all existing video descriptions.
Inserts after the Disclaimer line, before the hashtag block.

Run: python update_descriptions.py
"""

import os, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))

from config import YOUTUBE_CLIENT_SECRET_FILE, YOUTUBE_TOKEN_FILE

COPYRIGHT = (
    "\n🎵 All music is original and commercially licensed.\n"
    "Creative direction & visual artwork © DhunDetox."
)
DISCLAIMER = "⚠️ Disclaimer:"

VIDEO_IDS = [
    "wk6MkePq4iM",  # 2026-06-03
    "JM7g6gL7a7w",  # 2026-06-04
    "fHFOaqHfZIA",  # 2026-06-05
    "6PihxNUnN3Y",  # 2026-06-06
    "EDKaV-T4t1w",  # 2026-06-07
    "okKf27z3e3c",  # 2026-06-08
]


def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
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


def _insert_copyright(desc: str) -> tuple[str, bool]:
    """Insert copyright after disclaimer line. Returns (new_desc, was_changed)."""
    if "© DhunDetox." in desc:
        return desc, False  # already correct
    # Fix old "Dhun Detox" spelling if present
    if "© Dhun Detox." in desc:
        return desc.replace("© Dhun Detox.", "© DhunDetox."), True

    # Find disclaimer line and insert after it
    idx = desc.find(DISCLAIMER)
    if idx == -1:
        # No disclaimer found — append at end before hashtags
        lines = desc.rstrip().split("\n")
        # Find first hashtag line
        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                lines.insert(i, "")
                lines.insert(i, COPYRIGHT.strip())
                lines.insert(i, "")
                return "\n".join(lines), True
        # No hashtags either — just append
        return desc.rstrip() + "\n" + COPYRIGHT + "\n", True

    # Find end of disclaimer line
    end = desc.find("\n", idx)
    if end == -1:
        return desc + "\n" + COPYRIGHT, True

    return desc[:end] + "\n" + COPYRIGHT + desc[end:], True


def main():
    from googleapiclient.discovery import build

    creds   = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    for vid in VIDEO_IDS:
        # Fetch current snippet
        resp = youtube.videos().list(part="snippet", id=vid).execute()
        items = resp.get("items", [])
        if not items:
            print(f"[skip] {vid} — not found")
            continue

        snippet = items[0]["snippet"]
        title   = snippet.get("title", "")
        desc    = snippet.get("description", "")

        new_desc, changed = _insert_copyright(desc)
        if not changed:
            print(f"[skip] {vid} — already has copyright line")
            continue

        # Update
        youtube.videos().update(
            part="snippet",
            body={
                "id": vid,
                "snippet": {
                    "title":       title,
                    "description": new_desc,
                    "categoryId":  snippet.get("categoryId", "10"),
                    "tags":        snippet.get("tags", []),
                    "defaultLanguage": snippet.get("defaultLanguage", "en"),
                },
            },
        ).execute()
        print(f"[updated] {vid} — {title[:60]}")

    print("\nDone.")


if __name__ == "__main__":
    main()
