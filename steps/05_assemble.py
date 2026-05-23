"""
Step 5 — Video Assembly
Loops the static background image for the full audio duration, adds the music track,
overlays a title text bar at the bottom, and adds fade in/out.
Output: output/final_video.mp4
"""

import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OUTPUT_DIR

FINAL_VIDEO = os.path.join(OUTPUT_DIR, "final_video.mp4")
FONT_PATH   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts", "BebasNeue-Regular.ttf")


def _get_audio_duration(audio_path: str) -> float:
    """Parse duration from ffmpeg stderr — works without ffprobe."""
    import re
    r = subprocess.run(["ffmpeg", "-i", audio_path, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"Duration:\s+(\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise RuntimeError(f"[assemble] Could not read duration of {audio_path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def run(brain: dict, image_path: str, audio_path: str) -> str:
    title = brain["title"]
    audio_duration = _get_audio_duration(audio_path)
    print(f"[assemble] Audio={audio_duration:.0f}s, building video from static image...")

    # Clean video — no drawtext overlay (title lives on the thumbnail instead)
    filter_complex = (
        f"[0:v]"
        f"scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,"
        f"fade=t=in:st=0:d=2,"
        f"fade=t=out:st={audio_duration - 3}:d=3[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,      # loop static image
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(audio_duration),
        "-movflags", "+faststart",
        FINAL_VIDEO,
    ]

    print("[assemble] Running FFmpeg...")
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
    size_mb = os.path.getsize(FINAL_VIDEO) / 1_048_576
    print(f"[assemble] Saved {FINAL_VIDEO} ({size_mb:.1f} MB)")
    return FINAL_VIDEO


if __name__ == "__main__":
    stub = {"title": "Need Deep Rest? Raga Yaman on Sitar | 12 Min Indian Classical"}
    run(
        stub,
        os.path.join(OUTPUT_DIR, "background.png"),
        os.path.join(OUTPUT_DIR, "music.mp3"),
    )
