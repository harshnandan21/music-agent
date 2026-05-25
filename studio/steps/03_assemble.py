"""
Studio Step 3 — Assemble
Combines draft_dir/background.png (or .jpg) + draft_dir/music.mp3 into
draft_dir/video.mp4 using FFmpeg (static image loop + audio).
"""

import os, re, subprocess, sys

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)


def _get_audio_duration(path: str) -> float:
    r = subprocess.run(["ffmpeg", "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"Duration:\s+(\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise RuntimeError(f"[assemble] Cannot read duration of {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def _find_image(draft_dir: str) -> str:
    # Prefer explicitly named background, then any image that isn't the thumbnail
    SKIP = {"thumbnail.png", "thumbnail.jpg"}
    for name in ["background.png", "background.jpg", "background.jpeg"]:
        p = os.path.join(draft_dir, name)
        if os.path.exists(p):
            return p
    for f in sorted(os.listdir(draft_dir)):
        if f.lower().endswith((".png", ".jpg", ".jpeg")) and f not in SKIP:
            return os.path.join(draft_dir, f)
    raise FileNotFoundError(
        f"[assemble] No background image found in {draft_dir}. "
        "Drop an image file there and re-run --publish."
    )


def run(brain: dict, draft_dir: str) -> str:
    music_path = os.path.join(draft_dir, "music.mp3")
    if not os.path.exists(music_path):
        raise FileNotFoundError(f"[assemble] music.mp3 not found in {draft_dir}")

    image_path    = _find_image(draft_dir)
    audio_duration = _get_audio_duration(music_path)
    print(f"[assemble] Audio={audio_duration:.0f}s, image={os.path.basename(image_path)}")

    filter_complex = (
        f"[0:v]"
        f"scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,"
        f"fade=t=in:st=0:d=2,"
        f"fade=t=out:st={audio_duration - 3}:d=3[v]"
    )

    out_path = os.path.join(draft_dir, "video.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(audio_duration),
        "-movflags", "+faststart",
        out_path,
    ]
    print("[assemble] Running FFmpeg...")
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)

    size_mb = os.path.getsize(out_path) / 1_048_576
    print(f"[assemble] Saved {out_path} ({size_mb:.1f} MB)")
    return out_path
