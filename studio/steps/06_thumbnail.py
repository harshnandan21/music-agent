"""
Studio Step 6 — Thumbnail
5-zone DhunDetox layout:
  ① Top-left:   Hz badge (warm gold circle, deep indigo text)
  ② Top-right:  Mandala ornament (geometric gold spokes)
  ③ Center:     Hook text (Anton / Cormorant Garamond, warm gold)
  ④ Middle:     Raga · Instrument line (cream ivory)
  ⑤ Bottom:     Tagline strip (cream ivory) + lotus seal bottom-right

Brand colors: Deep Indigo #1A1F3A · Warm Gold #D4A857 · Cream Ivory #F5ECD7

Output: draft_dir/thumbnail.png  (1280×720)
"""

import math, os, sys

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)

W, H = 1280, 720

DEEP_INDIGO = (26,  31,  58)    # #1A1F3A
WARM_GOLD   = (212, 168, 87)    # #D4A857
CREAM_IVORY = (245, 236, 215)   # #F5ECD7
WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)

# Legacy aliases
GOLD  = WARM_GOLD
CREAM = CREAM_IVORY


def _load_font(path, size):
    from PIL import ImageFont
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    fallbacks = [
        os.path.join(ROOT_DIR, "assets", "fonts", "CormorantGaramond-Bold.ttf"),
        os.path.join(ROOT_DIR, "assets", "fonts", "Anton-Regular.ttf"),
        os.path.join(ROOT_DIR, "assets", "fonts", "BebasNeue-Regular.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial.ttf",
    ]
    for fb in fallbacks:
        if os.path.exists(fb):
            try:
                return ImageFont.truetype(fb, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def _th(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def _greedy_wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur_words, cur_w = [], [], 0
    sp = _tw(draw, " ", font)
    for w in words:
        ww = _tw(draw, w, font)
        if cur_words and cur_w + sp + ww > max_width:
            lines.append(" ".join(cur_words))
            cur_words, cur_w = [w], ww
        else:
            cur_words.append(w)
            cur_w = ww if not cur_w else cur_w + sp + ww
    if cur_words:
        lines.append(" ".join(cur_words))
    return lines


def _fit_text(draw, text, font_path, start_size, max_width, max_lines=2):
    for size in range(start_size, 28, -2):
        font = _load_font(font_path, size)
        lines = _greedy_wrap(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return lines, font, size
    font = _load_font(font_path, 30)
    return _greedy_wrap(draw, text, font, max_width), font, 30


def _draw_outlined(draw, x, cy, text, font, fill, outline_color=BLACK, outline_w=6, shadow=9):
    draw.text((x + shadow, cy + shadow), text, font=font, fill=(0, 0, 0, 160))
    for dx in range(-outline_w, outline_w + 1):
        for dy in range(-outline_w, outline_w + 1):
            if dx * dx + dy * dy <= outline_w * outline_w:
                draw.text((x + dx, cy + dy), text, font=font, fill=outline_color)
    draw.text((x, cy), text, font=font, fill=fill)
    return _th(draw, text, font)


def _draw_centered_outlined(draw, cy, text, font, fill, outline_color=BLACK, outline_w=6, shadow=9):
    tw = _tw(draw, text, font)
    x  = (W - tw) // 2
    return _draw_outlined(draw, x, cy, text, font, fill, outline_color, outline_w, shadow)


def _draw_centered_mixed(draw, cy, text, font, default_fill, gold_words,
                         outline_color=BLACK, outline_w=3, shadow=5):
    tw = _tw(draw, text, font)
    x  = (W - tw) // 2
    for word in text.split():
        ww   = _tw(draw, word, font)
        fill = WARM_GOLD if word.upper().strip("·&,|") in gold_words else default_fill
        draw.text((x + shadow, cy + shadow), word, font=font, fill=(0, 0, 0, 160))
        for dx in range(-outline_w, outline_w + 1):
            for dy in range(-outline_w, outline_w + 1):
                if dx * dx + dy * dy <= outline_w * outline_w:
                    draw.text((x + dx, cy + dy), word, font=font, fill=outline_color)
        draw.text((x, cy), word, font=font, fill=fill)
        x += _tw(draw, word + " ", font)


def _draw_hz_badge(draw, hz_text: str, font_path: str):
    """① Top-left: gold circle with Hz value in deep indigo."""
    cx, cy, r = 88, 84, 70
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WARM_GOLD)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=DEEP_INDIGO, width=5)
    ri = r - 10
    draw.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], outline=DEEP_INDIGO, width=2)

    # Split e.g. "432Hz" → "432" + "Hz"
    hz_clean = str(hz_text).replace("hz", "Hz")
    if "Hz" in hz_clean:
        num, lbl = hz_clean.split("Hz")[0].strip(), "Hz"
    else:
        num, lbl = hz_clean, ""

    font_num = _load_font(font_path, 38)
    font_lbl = _load_font(font_path, 22)
    num_w    = _tw(draw, num, font_num)
    lbl_w    = _tw(draw, lbl, font_lbl)

    draw.text((cx - num_w // 2, cy - 26), num, font=font_num, fill=DEEP_INDIGO)
    if lbl:
        draw.text((cx - lbl_w // 2, cy + 14), lbl, font=font_lbl, fill=DEEP_INDIGO)


def _draw_mandala(draw, cx: int, cy: int, r: int):
    """② Top-right: geometric mandala in warm gold."""
    for frac, width in [(1.0, 3), (0.72, 2), (0.48, 1), (0.26, 1)]:
        ri = int(r * frac)
        draw.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], outline=WARM_GOLD, width=width)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1  = cx + int(r * 0.28 * math.cos(rad))
        y1  = cy + int(r * 0.28 * math.sin(rad))
        x2  = cx + int(r * 0.86 * math.cos(rad))
        y2  = cy + int(r * 0.86 * math.sin(rad))
        draw.line([x1, y1, x2, y2], fill=WARM_GOLD, width=2)
    for angle in range(22, 360, 45):
        rad = math.radians(angle)
        px  = cx + int(r * 0.58 * math.cos(rad))
        py  = cy + int(r * 0.58 * math.sin(rad))
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=WARM_GOLD)


def _draw_lotus(draw, cx: int, cy: int, r: int):
    """⑤ Bottom-right: 8-petal lotus seal in warm gold."""
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        pr  = int(r * 0.50)
        px  = cx + int(pr * math.cos(rad))
        py  = cy + int(pr * math.sin(rad))
        pw, ph = int(r * 0.30), int(r * 0.18)
        draw.ellipse([px - pw, py - ph, px + pw, py + ph], outline=WARM_GOLD, width=2)
    rc = int(r * 0.22)
    draw.ellipse([cx - rc, cy - rc, cx + rc, cy + rc], fill=WARM_GOLD)


def run(brain: dict, draft_dir: str) -> str:
    from PIL import Image, ImageDraw

    for name in ["background_watermarked.png", "background.png", "background.jpg"]:
        bg_path = os.path.join(draft_dir, name)
        if os.path.exists(bg_path):
            break
    else:
        raise FileNotFoundError(f"[thumbnail] No background image found in {draft_dir}")

    img = Image.open(bg_path).convert("RGB").resize((W, H), Image.LANCZOS)

    FONTS_DIR = os.path.join(ROOT_DIR, "assets", "fonts")
    cormorant = os.path.join(FONTS_DIR, "CormorantGaramond-Bold.ttf")
    anton     = os.path.join(FONTS_DIR, "Anton-Regular.ttf")
    bebas     = os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf")
    hook_fp   = cormorant if os.path.exists(cormorant) else (anton if os.path.exists(anton) else bebas)
    label_fp  = bebas if os.path.exists(bebas) else hook_fp

    raga       = brain.get("raga", "")
    instrument = brain.get("instrument", "")
    hz         = brain.get("hz_frequency", "")
    hook_text  = brain.get("thumbnail_hook", "")
    instr_line = brain.get("thumbnail_instr", "")
    tagline    = brain.get("thumbnail_tagline", "")

    if not hook_text:
        title     = brain.get("title", "")
        hook_text = title.split("|")[0].strip().upper() if "|" in title else title.upper()
    if not instr_line:
        hz_part    = f" · {hz}" if hz else ""
        instr_line = f"{instrument.upper()} · RAAG {raga.upper()}{hz_part}"
    if not tagline:
        tagline = brain.get("use_case", "").title()

    hook_text  = hook_text.upper()
    instr_line = instr_line.upper()

    gold_words = {w for w in (raga + " " + instrument.replace("&", " ").replace(",", " ")).upper().split() if w}

    # ── Gradient overlays ──────────────────────────────────────────────────────
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov      = ImageDraw.Draw(overlay)

    for py in range(int(H * 0.30)):
        t = 1.0 - py / (H * 0.30)
        ov.line([(0, py), (W, py)], fill=(0, 0, 0, int(130 * t)))

    bot_start = int(H * 0.76)
    for py in range(bot_start, H):
        t = (py - bot_start) / (H - bot_start)
        ov.line([(0, py), (W, py)], fill=(0, 0, 0, int(210 * (t ** 0.4))))

    img  = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    PADDING = 48
    max_w   = W - PADDING * 2

    # ── ① Hz badge — top-left ─────────────────────────────────────────────────
    if hz:
        _draw_hz_badge(draw, str(hz), label_fp)

    # ── ② Mandala — top-right ─────────────────────────────────────────────────
    _draw_mandala(draw, W - 88, 84, 68)

    # ── ③ Hook text — centered, large ─────────────────────────────────────────
    lines_hook, font_hook, sz_hook = _fit_text(draw, hook_text, hook_fp, 148, max_w - 60, max_lines=2)
    lh_hook = int(sz_hook * 1.06)
    y = 18
    for line in lines_hook:
        _draw_centered_outlined(draw, y, line, font_hook,
                                fill=WARM_GOLD, outline_color=(40, 20, 0), outline_w=7, shadow=10)
        y += lh_hook

    y += 8

    # ── Gold divider ──────────────────────────────────────────────────────────
    div_w = min(W - PADDING * 4, 820)
    div_x = (W - div_w) // 2
    draw.rectangle([div_x, y, div_x + div_w, y + 4], fill=WARM_GOLD)
    y += 14

    # ── ④ Instrument · Raga · Hz line ─────────────────────────────────────────
    lines_instr, font_instr, sz_instr = _fit_text(draw, instr_line, label_fp, 68, max_w, max_lines=1)
    lh_instr = int(sz_instr * 1.08)
    for line in lines_instr:
        _draw_centered_mixed(draw, y, line, font_instr, CREAM_IVORY, gold_words,
                             outline_color=(30, 15, 0), outline_w=3, shadow=5)
        y += lh_instr

    # ── ⑤ Tagline in bottom strip ─────────────────────────────────────────────
    tag_lines, tag_font, tag_sz = _fit_text(draw, tagline, label_fp, 52, max_w - PADDING, max_lines=2)
    lh_tag  = int(tag_sz * 1.06)
    total_h = lh_tag * len(tag_lines)
    tag_y   = H - total_h - 22
    for line in tag_lines:
        _draw_centered_outlined(draw, tag_y, line, tag_font,
                                fill=CREAM_IVORY, outline_color=BLACK, outline_w=4, shadow=6)
        tag_y += lh_tag

    # ── Lotus seal — bottom-right ─────────────────────────────────────────────
    _draw_lotus(draw, W - 72, H - 72, 55)

    out_path = os.path.join(draft_dir, "thumbnail.png")
    img.save(out_path, "PNG")
    size_kb = os.path.getsize(out_path) // 1024
    print(f"[thumbnail] Saved {out_path} ({size_kb} KB)")
    return out_path
