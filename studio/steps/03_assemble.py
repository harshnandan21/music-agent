"""
Studio Step 3 — Assemble
Combines background + music.mp3 into video.mp4.

Video clip mode (preferred):
  Drop clip.mp4 (8-second Veo seamless loop) in the draft folder.
  Veo guarantees first frame == last frame, so the clip is looped
  directly with -stream_loop -1. No dissolve needed.

Static image mode (fallback):
  Drop background.png/jpg. Used when no clip.mp4 is found.
"""

import os, subprocess, sys

STUDIO_DIR   = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR     = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, STUDIO_DIR)

from utils import get_duration

SCALE_FILTER = (
    "scale=1920:1080:force_original_aspect_ratio=decrease,"
    "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
)


def _find_clip(draft_dir: str) -> str | None:
    p = os.path.join(draft_dir, "clip.mp4")
    return p if os.path.exists(p) else None


def _find_image(draft_dir: str) -> str:
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
        "Drop background.png or clip.mp4 and re-run --publish."
    )


def _assemble_from_clip(clip_path: str, music_path: str, duration: float, out_path: str):
    # Veo clips are seamless loops (first frame == last frame) — loop directly,
    # no dissolve processing needed.
    fade_out_start = duration - 3
    vf = (
        f"{SCALE_FILTER},"
        f"fade=t=in:st=0:d=2,"
        f"fade=t=out:st={fade_out_start}:d=3"
    )
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", clip_path,
        "-i", music_path,
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-movflags", "+faststart",
        out_path,
    ]
    print("[assemble] Assembling video from looped clip...")
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)


def _assemble_from_image(image_path: str, music_path: str, duration: float, out_path: str):
    filter_complex = (
        f"[0:v]{SCALE_FILTER},"
        f"fade=t=in:st=0:d=2,"
        f"fade=t=out:st={duration - 3}:d=3[v]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-movflags", "+faststart",
        out_path,
    ]
    print("[assemble] Assembling video from static image...")
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)


def run(brain: dict, draft_dir: str) -> str:
    music_path = os.path.join(draft_dir, "music.mp3")
    if not os.path.exists(music_path):
        raise FileNotFoundError(f"[assemble] music.mp3 not found in {draft_dir}")

    duration  = get_duration(music_path)
    out_path  = os.path.join(draft_dir, "video.mp4")
    clip_path = _find_clip(draft_dir)

    if clip_path:
        print(f"[assemble] clip.mp4 found — video loop mode")
        _assemble_from_clip(clip_path, music_path, duration, out_path)
    else:
        image_path = _find_image(draft_dir)
        print(f"[assemble] Audio={duration:.0f}s, image={os.path.basename(image_path)}")
        _assemble_from_image(image_path, music_path, duration, out_path)

    size_mb = os.path.getsize(out_path) / 1_048_576
    print(f"[assemble] Saved {out_path} ({size_mb:.1f} MB)")
    return out_path
