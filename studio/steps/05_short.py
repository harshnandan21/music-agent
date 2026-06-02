"""
Studio Step 5 — Short
Layout:
  - Full-bleed image (entire frame)
  - TOP: Hook question (2 lines, centered, with text-box bg) — grabs attention
  - BOTTOM: Now Playing card — raga, instruments, mood, CTA
Output: draft_dir/short.mp4
"""

import os, re, subprocess, sys, tempfile

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)

CLIP_START     = 30
CLIP_DUR       = 30
FONT_REL       = "assets/fonts/BebasNeue-Regular.ttf"
CHANNEL_HANDLE = "@DhunDetox"

# Card geometry (pixels in 1080x1920)
FADE_START  = 860
CARD_START  = 1190
GOLD_LINE_H = 5
CARD_BG     = (16, 9, 3, 225)
GOLD_COLOR  = (255, 210, 0, 235)
LOGO_SIZE   = 56


def _q(s: str) -> str:
    # Strip apostrophes and other chars that break FFmpeg's single-quote parser
    s = re.sub(r"['‘’“”]", "", s)
    return "'" + s + "'"


def _make_card_png(logo_src: str | None = None) -> str:
    import numpy as np
    from PIL import Image, ImageDraw

    arr = np.zeros((1920, 1080, 4), dtype=np.uint8)

    # Top fade (darkens just the top edge for hook text readability)
    top_h = 420
    ys = np.arange(top_h)
    arr[:top_h, :, 3] = (185 * (1 - ys / top_h))[:, None].astype(np.uint8)

    # Gradient fade transparent → card
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

    # Circular logo — top-right of card
    if logo_src and os.path.exists(logo_src):
        from PIL import ImageDraw as _ID
        logo = Image.open(logo_src).convert("RGBA")
        logo = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
        mask = Image.new("L", (LOGO_SIZE, LOGO_SIZE), 0)
        _ID.Draw(mask).ellipse((0, 0, LOGO_SIZE - 1, LOGO_SIZE - 1), fill=255)
        logo.putalpha(mask)
        img.paste(logo, (1080 - LOGO_SIZE - 50, CARD_START + GOLD_LINE_H + 14), logo)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, "PNG")
    return tmp.name


# ── Text helpers ──────────────────────────────────────────────────────────────

def _hook_lines(use_case: str, thumbnail_hook: str) -> tuple[str, str]:
    """Return two punchy apostrophe-free hook lines based on the use case."""
    uc = use_case.lower()
    if any(w in uc for w in ("overthink", "overactive", "racing")):
        return ("MIND RACING", "AT MIDNIGHT?")
    if any(w in uc for w in ("sleep", "insomnia", "night")):
        return ("WAKE UP", "AT 3AM AGAIN?")
    if any(w in uc for w in ("stress", "anxiety", "cortisol", "nervous")):
        return ("FEELING", "OVERWHELMED?")
    if any(w in uc for w in ("morning", "prana", "reset", "energy")):
        return ("NEED A", "MORNING RESET?")
    if any(w in uc for w in ("focus", "study", "clarity", "brain")):
        return ("NEED TO", "FOCUS NOW?")
    if any(w in uc for w in ("meditat", "yoga", "mindful")):
        return ("TIME TO", "MEDITATE?")
    if any(w in uc for w in ("relax", "unwind", "calm", "relief")):
        return ("NEED TO", "UNWIND?")
    # fallback: use thumbnail_hook, strip apostrophes
    hook = re.sub(r"['\"]", "", thumbnail_hook.strip().upper())
    words = hook.split()
    mid = max(1, len(words) // 2)
    return (" ".join(words[:mid]), " ".join(words[mid:]))


def _short_mood(use_case: str, thumbnail_hook: str) -> str:
    hook = (thumbnail_hook or "").strip().upper()
    if hook and len(hook) <= 22:
        return hook
    return " ".join(use_case.replace("_", " ").split()[:3]).upper()


def _instr_display(instrument: str) -> str:
    parts = re.split(r"[,&/]| and ", instrument, flags=re.IGNORECASE)
    cleaned = []
    for p in parts:
        p = p.strip().upper()
        p = re.sub(r'\b(FLUTE|GUITAR|VIOLIN|DRUM)\b', '', p).strip()
        if p:
            cleaned.append(p)
    return "  -  ".join(cleaned)


def _measure(text: str, fontsize: int) -> int:
    """Return pixel width of text at given size using PIL (accurate)."""
    from PIL import ImageFont
    font_path = os.path.join(ROOT_DIR, "assets", "fonts", "BebasNeue-Regular.ttf")
    try:
        font = ImageFont.truetype(font_path, fontsize)
        return int(font.getlength(text))
    except Exception:
        return int(len(text) * 0.62 * fontsize)


def _fit_fontsize(text: str, max_width: int, base: int, min_size: int = 60) -> int:
    """Scale base font size down until text fits within max_width."""
    w = _measure(text, base)
    if w <= max_width:
        return base
    return max(min_size, int(base * max_width / w))


def _raga_split(raga: str) -> tuple[str, str | None]:
    """Split multi-word raga into two lines for better fit and impact."""
    words = raga.split()
    if len(words) >= 2:
        mid = (len(words) + 1) // 2
        return " ".join(words[:mid]), " ".join(words[mid:])
    return raga, None


def _instr_fontsize(instr: str, max_width: int = 960, base: int = 42) -> int:
    return _fit_fontsize(instr, max_width, base, min_size=24)


# ── Main ──────────────────────────────────────────────────────────────────────

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
    mood_hz   = f"{mood}  -  {hz}" if hz else mood
    link_line = "FULL VIDEO IN DESCRIPTION"

    hook1, hook2  = _hook_lines(use_case, hook)
    raga_l1, raga_l2 = _raga_split(raga)
    # For split raga: use larger font since each line is shorter
    raga_base = 148 if raga_l2 else 148
    raga_fs   = _fit_fontsize(raga_l1, 960, raga_base)
    if raga_l2:
        raga_fs = min(raga_fs, _fit_fontsize(raga_l2, 960, raga_base))
    instr_fs  = _instr_fontsize(instr)
    hook_fs   = min(105, _fit_fontsize(hook1, 900, 105), _fit_fontsize(hook2, 900, 105))

    logo_src  = os.path.join(ROOT_DIR, "assets", "logo.png")
    card_path = _make_card_png(logo_src if os.path.exists(logo_src) else None)
    fp        = FONT_REL
    fade_out  = CLIP_DUR - 2

    # ── Y positions ───────────────────────────────────────────────────────────
    LX       = 55
    # Hook text (centered, top — uses the top gradient for bg, no drawbox)
    Y_HOOK1  = 58
    Y_HOOK2  = Y_HOOK1 + hook_fs + 8
    # Card text
    Y_HEADER = CARD_START + GOLD_LINE_H + 16
    Y_DECO   = Y_HEADER + 46
    Y_RAGA   = Y_DECO + 18
    # If raga splits into 2 lines, second line sits right below
    Y_RAGA2  = Y_RAGA + raga_fs + 4
    raga_block_h = (raga_fs * 2 + 4) if raga_l2 else raga_fs
    Y_INSTR  = Y_RAGA + raga_block_h + 14
    Y_MOOD   = Y_INSTR + instr_fs + 16
    Y_DIV    = Y_MOOD + 52
    Y_CTA    = Y_DIV + 20
    Y_LINK   = Y_CTA + 52

    try:
        parts = [
            # Full-bleed center crop
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[base]",
            # Overlay card + top fade (input 1)
            "[base][1:v]overlay=0:0[vg]",

            # ── TOP HOOK TEXT (no harsh drawbox — top gradient handles bg) ────
            f"[vg]drawtext=fontfile={_q(fp)}"
            f":text={_q(hook1)}"
            f":fontsize={hook_fs}:fontcolor=white"
            f":x=(w-text_w)/2:y={Y_HOOK1}"
            f":shadowcolor=black@0.95:shadowx=5:shadowy=5[h1]",

            f"[h1]drawtext=fontfile={_q(fp)}"
            f":text={_q(hook2)}"
            f":fontsize={hook_fs}:fontcolor=0xFFD700"
            f":x=(w-text_w)/2:y={Y_HOOK2}"
            f":shadowcolor=black@0.95:shadowx=5:shadowy=5[h2]",

            # ── CARD TEXT (left-aligned) ──────────────────────────────────────
            f"[h2]drawtext=fontfile={_q(fp)}"
            f":text='DHUNDETOX   -   RAGA'"
            f":fontsize=30:fontcolor=0xFFD700@0.75"
            f":x={LX}:y={Y_HEADER}"
            f":shadowcolor=black@0.5:shadowx=1:shadowy=1[t0]",

            # Decorative ornament
            f"[t0]drawbox=x={LX}:y={Y_DECO+3}:w=68:h=2:color=0xFFD700@0.45:t=fill[d1]",
            f"[d1]drawbox=x={LX+76}:y={Y_DECO-1}:w=10:h=10:color=0xFFD700@0.60:t=fill[d2]",
            f"[d2]drawbox=x={LX+94}:y={Y_DECO+3}:w=68:h=2:color=0xFFD700@0.45:t=fill[d3]",

            # Raga name line 1 — depth layer
            f"[d3]drawtext=fontfile={_q(fp)}"
            f":text={_q(raga_l1)}"
            f":fontsize={max(55, raga_fs-10)}:fontcolor=0x7A5200"
            f":x={LX+3}:y={Y_RAGA+4}"
            f":shadowcolor=black@0:shadowx=0:shadowy=0[ra]",
            # Raga name line 1 — gold
            f"[ra]drawtext=fontfile={_q(fp)}"
            f":text={_q(raga_l1)}"
            f":fontsize={raga_fs}:fontcolor=0xFFD700"
            f":x={LX}:y={Y_RAGA}"
            f":shadowcolor=0x0C0400@0.9:shadowx=4:shadowy=4[rb]",
        ]

        # Raga name line 2 (if split)
        prev = "rb"
        if raga_l2:
            parts += [
                f"[rb]drawtext=fontfile={_q(fp)}"
                f":text={_q(raga_l2)}"
                f":fontsize={max(55, raga_fs-10)}:fontcolor=0x7A5200"
                f":x={LX+3}:y={Y_RAGA2+4}"
                f":shadowcolor=black@0:shadowx=0:shadowy=0[rc]",
                f"[rc]drawtext=fontfile={_q(fp)}"
                f":text={_q(raga_l2)}"
                f":fontsize={raga_fs}:fontcolor=0xFFD700"
                f":x={LX}:y={Y_RAGA2}"
                f":shadowcolor=0x0C0400@0.9:shadowx=4:shadowy=4[rd]",
            ]
            prev = "rd"

        parts += [
            # Instruments
            f"[{prev}]drawtext=fontfile={_q(fp)}"
            f":text={_q(instr)}"
            f":fontsize={instr_fs}:fontcolor=white@0.80"
            f":x={LX}:y={Y_INSTR}"
            f":shadowcolor=black@0.4:shadowx=1:shadowy=1[t2]",

            # Mood - Hz
            f"[t2]drawtext=fontfile={_q(fp)}"
            f":text={_q(mood_hz)}"
            f":fontsize=38:fontcolor=white@0.65"
            f":x={LX}:y={Y_MOOD}"
            f":shadowcolor=black@0.3:shadowx=1:shadowy=1[t3]",

            # Divider
            f"[t3]drawbox=x={LX}:y={Y_DIV}:w={1080-LX*2}:h=1:color=white@0.20:t=fill[t4]",

            # CTA
            f"[t4]drawtext=fontfile={_q(fp)}"
            f":text='>> WATCH FULL VERSION'"
            f":fontsize=40:fontcolor=0xFFD700"
            f":x={LX}:y={Y_CTA}"
            f":shadowcolor=black@0.6:shadowx=2:shadowy=2[t5]",

            # Link
            f"[t5]drawtext=fontfile={_q(fp)}"
            f":text={_q(link_line)}"
            f":fontsize=32:fontcolor=white@0.62"
            f":x={LX}:y={Y_LINK}"
            f":shadowcolor=black@0.4:shadowx=1:shadowy=1,"
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

        print(f"[short] Hook: '{hook1} / {hook2}'  Raga font: {raga_fs}px  Instr font: {instr_fs}px")
        print("[short] Generating Short...")
        subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL, cwd=ROOT_DIR)

        size_mb = os.path.getsize(out_path) / 1_048_576
        print(f"[short] Saved {out_path} ({size_mb:.1f} MB)")
        return out_path

    finally:
        try:
            os.unlink(card_path)
        except Exception:
            pass
