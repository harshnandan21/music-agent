"""
Studio Step 6 — Thumbnail
Generates thumbnail.png in the draft folder from the background image.

Layout:
  - Hook text: large, gold, centered at top (e.g. "CAN'T FALL ASLEEP?")
  - Raga · Hz line: centered below hook, cream/gold
  - Tagline: centered in dark bottom strip
  - Subtle dark gradient at top and bottom so text pops on any background

Output: draft_dir/thumbnail.png  (1280×720)
"""

import os, sys

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)

W, H    = 1280, 720
GOLD    = (255, 213, 60)
CREAM   = (255, 245, 210)
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)


def _load_font(path, size):
    from PIL import ImageFont
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for fb in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/Arial.ttf"]:
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
        fill = GOLD if word.upper().strip("·&,|") in gold_words else default_fill
        draw.text((x + shadow, cy + shadow), word, font=font, fill=(0, 0, 0, 160))
        for dx in range(-outline_w, outline_w + 1):
            for dy in range(-outline_w, outline_w + 1):
                if dx * dx + dy * dy <= outline_w * outline_w:
                    draw.text((x + dx, cy + dy), word, font=font, fill=outline_color)
        draw.text((x, cy), word, font=font, fill=fill)
        x += _tw(draw, word + " ", font)


def run(brain: dict, draft_dir: str) -> str:
    from PIL import Image, ImageDraw

    # Find background image
    for name in ["background_watermarked.png", "background.png", "background.jpg"]:
        bg_path = os.path.join(draft_dir, name)
        if os.path.exists(bg_path):
            break
    else:
        raise FileNotFoundError(f"[thumbnail] No background image found in {draft_dir}")

    img = Image.open(bg_path).convert("RGB").resize((W, H), Image.LANCZOS)

    FONTS_DIR = os.path.join(ROOT_DIR, "assets", "fonts")
    bebas     = os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf")
    anton     = os.path.join(FONTS_DIR, "Anton-Regular.ttf")
    hook_fp   = anton if os.path.exists(anton) else bebas

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

    # ── Gradient overlays ─────────────────────────────────────────────────────
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov      = ImageDraw.Draw(overlay)

    # Top 28%: dark gradient so hook pops
    for py in range(int(H * 0.28)):
        t = 1.0 - py / (H * 0.28)
        ov.line([(0, py), (W, py)], fill=(0, 0, 0, int(140 * t)))

    # Bottom 22%: dark strip for tagline
    bot_start = int(H * 0.78)
    for py in range(bot_start, H):
        t = (py - bot_start) / (H - bot_start)
        ov.line([(0, py), (W, py)], fill=(0, 0, 0, int(220 * (t ** 0.4))))

    img  = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    PADDING = 48
    max_w   = W - PADDING * 2

    # ── Hook: large gold centered at top ──────────────────────────────────────
    lines_hook, font_hook, sz_hook = _fit_text(draw, hook_text, hook_fp, 155, max_w, max_lines=2)
    lh_hook = int(sz_hook * 1.06)
    y = 18
    for line in lines_hook:
        _draw_centered_outlined(draw, y, line, font_hook,
                                fill=GOLD, outline_color=(80, 40, 0), outline_w=7, shadow=10)
        y += lh_hook

    y += 8

    # ── Gold divider ──────────────────────────────────────────────────────────
    div_w = min(W - PADDING * 4, 820)
    div_x = (W - div_w) // 2
    draw.rectangle([div_x, y, div_x + div_w, y + 4], fill=GOLD)
    y += 14

    # ── Instrument · Raga · Hz line ───────────────────────────────────────────
    lines_instr, font_instr, sz_instr = _fit_text(draw, instr_line, bebas, 68, max_w, max_lines=1)
    lh_instr = int(sz_instr * 1.08)
    for line in lines_instr:
        _draw_centered_mixed(draw, y, line, font_instr, CREAM, gold_words,
                             outline_color=(50, 25, 0), outline_w=3, shadow=5)
        y += lh_instr

    # ── Tagline in bottom strip ───────────────────────────────────────────────
    tag_lines, tag_font, tag_sz = _fit_text(draw, tagline, bebas, 52, max_w - PADDING, max_lines=2)
    lh_tag    = int(tag_sz * 1.06)
    total_h   = lh_tag * len(tag_lines)
    tag_y     = H - total_h - 20
    for line in tag_lines:
        _draw_centered_outlined(draw, tag_y, line, tag_font,
                                fill=WHITE, outline_color=BLACK, outline_w=4, shadow=6)
        tag_y += lh_tag

    out_path = os.path.join(draft_dir, "thumbnail.png")
    img.save(out_path, "PNG")
    size_kb = os.path.getsize(out_path) // 1024
    print(f"[thumbnail] Saved {out_path} ({size_kb} KB)")
    return out_path
