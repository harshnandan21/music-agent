"""
Studio Step 5 — Short
"Now Playing" card layout:
  - Full-bleed image (top 62%)
  - Gradient fade into dark warm card (bottom 38%)
  - Left-aligned text: channel brand, raga, instruments, mood, Hz, link
Output: draft_dir/short.mp4
"""

import os, re, subprocess, sys, tempfile

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)

CLIP_START   = 30
CLIP_DUR     = 30
FONT_REL     = "assets/fonts/BebasNeue-Regular.ttf"
CHANNEL_HANDLE = "@DhunDetox"

# Card geometry (pixels in 1080x1920)
FADE_START   = 880    # where gradient fade begins (longer cinematic blend)
CARD_START   = 1190   # where solid dark card begins (gold line here)
GOLD_LINE_H  = 5      # height of accent line
CARD_BG      = (16, 9, 3, 222)   # warm amber-black
GOLD_COLOR   = (255, 210, 0, 235)
LOGO_SIZE    = 58     # circular logo diameter in the card


def _q(s: str) -> str:
    return "'" + s.replace("'", "\\'") + "'"


def _make_card_png(logo_src: str | None = None) -> str:
    """PIL overlay: subtle top fade + warm dark card + gold line + optional logo."""
    import numpy as np
    from PIL import Image, ImageDraw

    arr = np.zeros((1920, 1080, 4), dtype=np.uint8)

    # Subtle top fade
    top_h = 180
    ys = np.arange(top_h)
    arr[:top_h, :, 3] = (150 * (1 - ys / top_h))[:, None].astype(np.uint8)

    # Gradient fade transparent → card opacity
    fade_h = CARD_START - FADE_START
    ys2 = np.arange(fade_h)
    alpha_fade = (CARD_BG[3] * ys2 / fade_h).astype(np.uint8)
    arr[FADE_START:CARD_START, :, 0] = CARD_BG[0]
    arr[FADE_START:CARD_START, :, 1] = CARD_BG[1]
    arr[FADE_START:CARD_START, :, 2] = CARD_BG[2]
    arr[FADE_START:CARD_START, :, 3] = alpha_fade[:, None]

    # Solid card
    arr[CARD_START:, :, :3] = CARD_BG[:3]
    arr[CARD_START:, :, 3]  = CARD_BG[3]

    # Gold accent line
    gl_end = CARD_START + GOLD_LINE_H
    arr[CARD_START:gl_end, :, :] = GOLD_COLOR

    img = Image.fromarray(arr, mode="RGBA")

    # Circular logo — top-right of card header
    if logo_src and os.path.exists(logo_src):
        logo = Image.open(logo_src).convert("RGBA")
        logo = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
        mask = Image.new("L", (LOGO_SIZE, LOGO_SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, LOGO_SIZE - 1, LOGO_SIZE - 1), fill=255)
        logo.putalpha(mask)
        logo_x = 1080 - LOGO_SIZE - 50
        logo_y = CARD_START + GOLD_LINE_H + 14
        img.paste(logo, (logo_x, logo_y), logo)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, "PNG")
    return tmp.name


def _short_mood(use_case: str, hook: str) -> str:
    hook = (hook or "").strip().upper()
    if hook and len(hook) <= 22:
        return hook
    return " ".join(use_case.replace("_", " ").split()[:3]).upper()


def _instr_display(instrument: str) -> str:
    parts = re.split(r"[,&/]| and ", instrument, flags=re.IGNORECASE)
    return "  ·  ".join(p.strip().upper() for p in parts if p.strip())


def run(brain: dict, draft_dir: str) -> str:
    video_path = os.path.join(draft_dir, "video.mp4")
    out_path   = os.path.join(draft_dir, "short.mp4")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"[short] video.mp4 not found in {draft_dir}")

    raga      = brain.get("raga", "").upper()
    instr     = _instr_display(brain.get("instrument", ""))
    use_case  = brain.get("use_case", "").replace("_", " ")
    hook      = brain.get("thumbnail_hook", "")
    hz_raw    = str(brain.get("hz_frequency", "")).strip()
    hz_num    = re.sub(r"[^0-9]", "", hz_raw)
    hz        = f"{hz_num} Hz" if hz_num else ""
    mood      = _short_mood(use_case, hook)
    main_id   = brain.get("main_video_id", "")

    # Bottom info line: mood · hz
    mood_hz = f"{mood}  ·  {hz}" if hz else mood

    link_line = "FULL VIDEO IN DESCRIPTION"

    logo_src  = os.path.join(ROOT_DIR, "assets", "logo.png")
    card_path = _make_card_png(logo_src if os.path.exists(logo_src) else None)
    fp        = FONT_REL
    fade_out  = CLIP_DUR - 2

    # Left margin for all card text
    LX = 55
    # Text y positions — spread across full card height (1274→1900)
    Y_HEADER = CARD_START + GOLD_LINE_H + 16   # 1290  "DHUNDETOX · RAGA"
    Y_RAGA   = Y_HEADER + 42                   # 1332  raga name (big)
    Y_INSTR  = Y_RAGA + 148                    # 1480  instruments
    Y_MOOD   = Y_INSTR + 62                    # 1542  mood · hz
    Y_DIV    = Y_MOOD + 62                     # 1604  divider
    Y_CTA    = Y_DIV + 24                      # 1628  CTA
    Y_LINK   = Y_CTA + 56                      # 1684  link

    try:
        parts = [
            # Full-bleed center crop
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[base]",
            # Overlay card (input 1)
            "[base][1:v]overlay=0:0[vg]",

            # ── CARD TEXT (left-aligned) ──────────────────────────────────────
            # Single header line: brand · category
            f"[vg]drawtext=fontfile={_q(fp)}"
            f":text='DHUNDETOX   ·   RAGA'"
            f":fontsize=32:fontcolor=0xFFD700@0.80"
            f":x={LX}:y={Y_HEADER}"
            f":shadowcolor=black@0.6:shadowx=1:shadowy=1[t0]",

            # Raga name — dominant, large, warm shadow
            f"[t0]drawtext=fontfile={_q(fp)}"
            f":text={_q(raga)}"
            f":fontsize=142:fontcolor=white"
            f":x={LX}:y={Y_RAGA}"
            f":shadowcolor=0x3D1F00@0.95:shadowx=5:shadowy=5[t1]",

            # Instruments — bright enough to read clearly
            f"[t1]drawtext=fontfile={_q(fp)}"
            f":text={_q(instr)}"
            f":fontsize=44:fontcolor=white@0.80"
            f":x={LX}:y={Y_INSTR}"
            f":shadowcolor=black@0.5:shadowx=2:shadowy=2[t2]",

            # Mood · Hz — slightly dimmer but still readable
            f"[t2]drawtext=fontfile={_q(fp)}"
            f":text={_q(mood_hz)}"
            f":fontsize=40:fontcolor=white@0.68"
            f":x={LX}:y={Y_MOOD}"
            f":shadowcolor=black@0.4:shadowx=1:shadowy=1[t3]",

            # Thin divider
            f"[t3]drawbox=x={LX}:y={Y_DIV}:w={1080-LX*2}:h=1:color=white@0.22:t=fill[t4]",

            # CTA
            f"[t4]drawtext=fontfile={_q(fp)}"
            f":text='>> WATCH FULL VERSION'"
            f":fontsize=40:fontcolor=0xFFD700"
            f":x={LX}:y={Y_CTA}"
            f":shadowcolor=black@0.7:shadowx=2:shadowy=2[t5]",

            # Link — visible and readable
            f"[t5]drawtext=fontfile={_q(fp)}"
            f":text={_q(link_line)}"
            f":fontsize=34:fontcolor=white@0.72"
            f":x={LX}:y={Y_LINK}"
            f":shadowcolor=black@0.5:shadowx=1:shadowy=1,"
            f"fade=t=in:st=0:d=1,"
            f"fade=t=out:st={fade_out}:d=2[v]",
        ]

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(CLIP_START),
            "-i", video_path,
            "-loop", "1", "-i", card_path,
            "-t", str(CLIP_DUR),
            "-filter_complex", ";".join(parts),
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            out_path,
        ]

        print("[short] Generating Short (Now Playing card layout)...")
        subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL, cwd=ROOT_DIR)

        size_mb = os.path.getsize(out_path) / 1_048_576
        print(f"[short] Saved {out_path} ({size_mb:.1f} MB)")
        return out_path

    finally:
        try:
            os.unlink(card_path)
        except Exception:
            pass
