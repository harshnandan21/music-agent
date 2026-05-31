"""
Studio Step 3 — Assemble
Combines background + music.mp3 into video.mp4.

Clip mode (preferred):
  Drop clip.mp4 (animated seamless loop) in the draft folder.
  Clips are looped with 0.5s xfade dissolve transitions.

Static image mode (fallback):
  Drop background.png/jpg. Used when no clip.mp4 is found.
"""

import math, os, subprocess, sys

STUDIO_DIR   = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR     = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, STUDIO_DIR)

from utils import get_duration

SCALE_FILTER = (
    "scale=1920:1080:force_original_aspect_ratio=decrease,"
    "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
)
LOGO_SIZE    = 80
LOGO_PADDING = 20
XFADE_DUR    = 0.5


def _make_circular_logo() -> str | None:
    """Create/cache 80px circular logo PNG. Returns path or None if logo missing."""
    from PIL import Image, ImageDraw
    src = os.path.join(ROOT_DIR, "assets", "logo.png")
    if not os.path.exists(src):
        return None
    out = os.path.join(ROOT_DIR, "assets", "logo_overlay.png")
    logo = Image.open(src).convert("RGBA")
    logo = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
    mask = Image.new("L", (LOGO_SIZE, LOGO_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, LOGO_SIZE - 1, LOGO_SIZE - 1), fill=255)
    logo.putalpha(mask)
    logo.save(out, "PNG")
    return out


def _stamp_logo(bg_path: str) -> str:
    """Stamp circular brand logo at bottom-right of background image."""
    from PIL import Image
    logo_overlay = _make_circular_logo()
    if not logo_overlay:
        return bg_path
    bg   = Image.open(bg_path).convert("RGBA")
    logo = Image.open(logo_overlay).convert("RGBA")
    x = bg.width  - LOGO_SIZE - LOGO_PADDING
    y = bg.height - LOGO_SIZE - LOGO_PADDING
    bg.paste(logo, (x, y), logo)
    out = bg_path.replace(".png", "_watermarked.png")
    bg.convert("RGB").save(out, "PNG")
    return out


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
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", clip_path],
        capture_output=True, text=True, check=True,
    )
    clip_dur      = float(probe.stdout.strip())
    effective_dur = clip_dur - XFADE_DUR
    n_clips       = max(2, math.ceil((duration - clip_dur) / effective_dur) + 1)

    logo_path = _make_circular_logo()
    has_logo  = logo_path is not None

    inputs = []
    for _ in range(n_clips):
        inputs += ["-i", clip_path]
    inputs += ["-i", music_path]
    if has_logo:
        inputs += ["-i", logo_path]

    music_idx      = n_clips
    logo_idx       = n_clips + 1
    fade_out_start = duration - 3

    # Scale all clips to 1920x1080
    parts = [f"[{i}:v]{SCALE_FILTER}[sv{i}]" for i in range(n_clips)]

    # Xfade dissolve chain
    prev = "[sv0]"
    for i in range(1, n_clips):
        offset = i * effective_dur
        label  = f"[xf{i}]"
        parts.append(
            f"{prev}[sv{i}]xfade=transition=dissolve:duration={XFADE_DUR}:offset={offset:.3f}{label}"
        )
        prev = label

    # Fade in/out
    parts.append(f"{prev}fade=t=in:st=0:d=2,fade=t=out:st={fade_out_start:.1f}:d=3[vfade]")

    # Logo overlay
    if has_logo:
        parts.append(f"[vfade][{logo_idx}:v]overlay=W-w-{LOGO_PADDING}:H-h-{LOGO_PADDING}:format=auto[v]")
        video_map = "[v]"
    else:
        video_map = "[vfade]"

    cmd = [
        "ffmpeg", "-y",
    ] + inputs + [
        "-filter_complex", ";".join(parts),
        "-map", video_map,
        "-map", f"{music_idx}:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "256k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-movflags", "+faststart",
        out_path,
    ]
    print(f"[assemble] Assembling {n_clips} clips with dissolve transitions...")
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
        "-c:a", "aac", "-b:a", "256k",
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
        image_path = _stamp_logo(image_path)
        print(f"[assemble] Audio={duration:.0f}s, image={os.path.basename(image_path)}")
        _assemble_from_image(image_path, music_path, duration, out_path)

    size_mb = os.path.getsize(out_path) / 1_048_576
    print(f"[assemble] Saved {out_path} ({size_mb:.1f} MB)")
    return out_path
