"""Shared utilities for studio steps."""
import re, subprocess


def get_duration(path: str) -> float:
    """Return audio/video duration in seconds using ffmpeg."""
    r = subprocess.run(
        ["ffmpeg", "-i", path, "-f", "null", "-"],
        capture_output=True, text=True,
    )
    m = re.search(r"Duration:\s+(\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise RuntimeError(f"Cannot read duration of {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
