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
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())


def run(brain: dict, image_path: str, audio_path: str) -> str:
    title = brain["title"]
    audio_duration = _get_audio_duration(audio_path)
    print(f"[assemble] Audio={audio_duration:.0f}s, building video from static image...")

    safe_title = title.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")
    font_arg = FONT_PATH if os.path.exists(FONT_PATH) else ""
    fontfile_clause = f"fontfile={font_arg}:" if font_arg else ""

    filter_complex = (
        f"[0:v]"
        f"scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,"
        f"drawtext={fontfile_clause}"
        f"text='{safe_title}':"
        f"fontcolor=white:fontsize=52:x=(w-text_w)/2:y=h-80:"
        f"box=1:boxcolor=black@0.55:boxborderw=12,"
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
    subprocess.run(cmd, check=True)
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
