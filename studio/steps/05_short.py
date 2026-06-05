"""
Studio Step 5 — Short
Generates a 30-second YouTube Short by:
  1. Calling Gemini Imagen to create a complete 9:16 portrait image
     (Gemini designs ALL text: hook, raga title, instruments, Hz, brand, CTA)
  2. Combining the portrait image with 30s of audio (fade in/out)
Output: draft_dir/short.mp4
"""

import os, re, subprocess, sys

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)

CLIP_START = 30   # seconds into the audio to start the clip
CLIP_DUR   = 60   # Short duration in seconds


# ── Image generation ──────────────────────────────────────────────────────────

def _build_prompt(brain: dict) -> str:
    title    = brain.get("title", "")
    raga     = brain.get("raga", "")
    instr    = brain.get("instrument", "")
    hz       = brain.get("hz_frequency", "")
    tagline  = brain.get("thumbnail_tagline", "")
    use_case = brain.get("use_case", "").replace("_", " ")

    return f"""
Create a complete YouTube Shorts image (9:16 vertical, 1080x1920 pixels).

YouTube video context:
Title: {title}
Tagline: {tagline}
Raga: {raga}
Instruments: {instr}
Frequency: {hz}
Use case: {use_case}

Design a COMPLETE SHORT IMAGE — include all key information as beautiful typography integrated into the image. It should work as a standalone poster that immediately tells viewers what this music is and why they need it.

Design requirements:
- A compelling hook question at the TOP (speak directly to the viewer's emotion based on the use case — e.g. if it is a midnight/sleep raga, speak to someone who cannot sleep)
- The raga name as the HERO typography element (large, prominent, beautiful)
- Key music info: instruments and frequency
- Channel name: DhunDetox
- A subtle call-to-action at the BOTTOM

Visual style: Cinematic Indian classical music poster. Rich, atmospheric, premium quality. Match the scene, lighting, and color palette to the raga mood and its time of day. Think: Bollywood poster meets Apple Music artwork meets Indian classical tradition. All text elements should be artistically integrated into the composition, not just overlaid.

Technical: Portrait 9:16 only. No watermarks. No borders.
""".strip()


def _generate_short_image(brain: dict, draft_dir: str) -> str:
    """Call Gemini to generate a complete Short portrait image. Returns path."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, ".env"))

    sys.path.insert(0, ROOT_DIR)
    from config import GEMINI_API_KEY, IMAGEN_MODEL
    from google import genai
    from google.genai import types
    from io import BytesIO
    from PIL import Image

    client   = genai.Client(api_key=GEMINI_API_KEY)
    prompt   = _build_prompt(brain)
    out_path = os.path.join(draft_dir, "short_bg.png")

    print("[short] Generating Short image via Gemini...")
    response = client.models.generate_content(
        model=IMAGEN_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    img_bytes = next(
        (p.inline_data.data for p in response.candidates[0].content.parts if p.inline_data),
        None,
    )
    if not img_bytes:
        raise RuntimeError("[short] Gemini returned no image")

    img = Image.open(BytesIO(img_bytes)).resize((1080, 1920), Image.LANCZOS)
    img.save(out_path, "PNG")
    size_kb = os.path.getsize(out_path) // 1024
    print(f"[short] Portrait image saved ({size_kb} KB)")
    return out_path


# ── Audio discovery ───────────────────────────────────────────────────────────

def _find_audio(draft_dir: str) -> str:
    """Return audio path: music.mp3 > any .wav > audio extracted from video.mp4"""
    mp3 = os.path.join(draft_dir, "music.mp3")
    if os.path.exists(mp3):
        return mp3

    for f in sorted(os.listdir(draft_dir)):
        if f.lower().endswith(".wav"):
            return os.path.join(draft_dir, f)

    # Last resort: extract audio from video.mp4
    video = os.path.join(draft_dir, "video.mp4")
    if os.path.exists(video):
        tmp_audio = os.path.join(draft_dir, "short_audio_tmp.aac")
        subprocess.run(
            ["ffmpeg", "-y", "-i", video, "-vn", "-c:a", "aac", "-b:a", "192k", tmp_audio],
            check=True, stdin=subprocess.DEVNULL, capture_output=True,
        )
        return tmp_audio

    raise FileNotFoundError(f"[short] No audio found in {draft_dir}")


# ── Assembly ──────────────────────────────────────────────────────────────────

def run(brain: dict, draft_dir: str) -> str:
    out_path   = os.path.join(draft_dir, "short.mp4")
    img_path   = _generate_short_image(brain, draft_dir)
    audio_path = _find_audio(draft_dir)

    print(f"[short] Audio: {os.path.basename(audio_path)}")
    print("[short] Assembling Short...")

    fade_out = CLIP_DUR - 2
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-ss", str(CLIP_START), "-i", audio_path,
        "-t", str(CLIP_DUR),
        "-vf", f"scale=1080:1920,fade=t=in:st=0:d=1,fade=t=out:st={fade_out}:d=2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-shortest",
        out_path,
    ]
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)

    size_mb = os.path.getsize(out_path) / 1_048_576
    print(f"[short] Saved {out_path} ({size_mb:.1f} MB)")
    return out_path
