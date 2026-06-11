"""Shared utilities for studio steps."""
import re, subprocess


def get_duration(path: str) -> float:
    """Return audio/video duration in seconds using ffprobe (reads header, no decode)."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())
