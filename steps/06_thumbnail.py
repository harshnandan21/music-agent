"""
Step 6 — Thumbnail Generation
Layout matching DhunDetox reference style:
  - Full Madhubani background visible (no heavy overlay)
  - Hook text: CENTERED at top, very large, warm gold with thick dark outline
  - Instrument · Raga line: centered below hook, cream white
  - Tagline: centered in a dark strip at the bottom
Output: output/thumbnail.jpg  (1280×720, quality 95)
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OUTPUT_DIR

THUMBNAIL_FILE = os.path.join(OUTPUT_DIR, "thumbnail.jpg")
W, H    = 1280, 720
GOLD    = (255, 213, 60)
CREAM   = (255, 245, 210)
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
DARK    = (15,  8,   0)
ORANGE  = (220, 120, 20)


# ── Font helpers ──────────────────────────────────────────────────────────────

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


# ── Text rendering ────────────────────────────────────────────────────────────

def _draw_centered_outlined(draw, cy, text, font, fill, outline_color=BLACK, outline_w=5, shadow=8):
    """Draw text centered at x, positioned at y=cy, with thick circular outline + shadow."""
    tw = _tw(draw, text, font)
    x = (W - tw) // 2

    # Drop shadow
    draw.text((x + shadow, cy + shadow), text, font=font, fill=(0, 0, 0, 160))

    # Thick circular outline
    for dx in range(-outline_w, outline_w + 1):
        for dy in range(-outline_w, outline_w + 1):
            if dx * dx + dy * dy <= outline_w * outline_w:
                draw.text((x + dx, cy + dy), text, font=font, fill=outline_color)

    draw.text((x, cy), text, font=font, fill=fill)
    return _th(draw, text, font)


def _draw_centered_mixed(draw, cy, text, font, default_fill, gold_words,
                         outline_color=BLACK, outline_w=3, shadow=5):
    """Center a line; words in gold_words rendered in GOLD, rest in default_fill."""
    tw = _tw(draw, text, font)
    x  = (W - tw) // 2

    for word in text.split():
        ww    = _tw(draw, word, font)
        fill  = GOLD if word.upper().strip("·&,") in gold_words else default_fill
        # Shadow
        draw.text((x + shadow, cy + shadow), word, font=font, fill=(0, 0, 0, 160))
        # Outline
        for dx in range(-outline_w, outline_w + 1):
            for dy in range(-outline_w, outline_w + 1):
                if dx * dx + dy * dy <= outline_w * outline_w:
                    draw.text((x + dx, cy + dy), word, font=font, fill=outline_color)
        draw.text((x, cy), word, font=font, fill=fill)
        x += _tw(draw, word + " ", font)


# ── Main ──────────────────────────────────────────────────────────────────────

def run(brain: dict, image_path: str) -> str:
    from PIL import Image, ImageDraw

    img = Image.open(image_path).convert("RGB").resize((W, H), Image.LANCZOS)

    FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
    bebas = os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf")
    anton = os.path.join(FONTS_DIR, "Anton-Regular.ttf")
    hook_fp   = anton if os.path.exists(anton) else bebas
    instr_fp  = bebas

    raga       = brain.get("raga", "")
    instrument = brain.get("instrument", "")

    hook_text  = brain.get("thumbnail_hook", "")
    instr_line = brain.get("thumbnail_instr", "") or brain.get("thumbnail_instrument_line", "")
    tagline    = brain.get("thumbnail_tagline", "")

    if not hook_text:
        title     = brain.get("title", "")
        hook_text = title.split("|")[0].strip().upper() if "|" in title else title.upper()
    if not instr_line:
        instr_line = f"{instrument.upper()} · RAAG {raga.upper()}" if raga else instrument.upper()
    if not tagline:
        tagline = brain.get("use_case", "").title()

    hook_text  = hook_text.upper()
    instr_line = instr_line.upper()

    # Gold words = raga + all instrument words
    clean_instr = instrument.replace("&", " ").replace(",", " ")
    gold_words  = {w for w in (raga + " " + clean_instr).upper().split() if w}

    # ── Overlay: only a bottom dark strip + very subtle top shade ────────────
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)

    # Top 22%: light shade so hook text pops (max 55% opacity at very top)
    for py in range(int(H * 0.22)):
        t = 1.0 - py / (H * 0.22)
        ov.line([(0, py), (W, py)], fill=(0, 0, 0, int(55 * t)))

    # Bottom 22%: solid-ish dark strip for tagline
    bot_start = int(H * 0.78)
    for py in range(bot_start, H):
        t = (py - bot_start) / (H - bot_start)
        ov.line([(0, py), (W, py)], fill=(0, 0, 0, int(220 * (t ** 0.4))))

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    PADDING = 48
    max_w   = W - PADDING * 2

    # ── Hook: centered at top, huge warm-gold text ────────────────────────────
    lines_hook, font_hook, sz_hook = _fit_text(draw, hook_text, hook_fp, 150, max_w, max_lines=2)
    lh_hook = int(sz_hook * 1.06)

    y = 22
    for line in lines_hook:
        _draw_centered_outlined(draw, y, line, font_hook,
                                fill=GOLD, outline_color=(90, 45, 0), outline_w=6, shadow=9)
        y += lh_hook

    y += 6

    # ── Thin gold divider ─────────────────────────────────────────────────────
    div_w = min(W - PADDING * 4, 820)
    div_x = (W - div_w) // 2
    draw.rectangle([div_x, y, div_x + div_w, y + 4], fill=GOLD)
    y += 14

    # ── Instrument · Raga line: centered, cream/gold mixed ────────────────────
    lines_instr, font_instr, sz_instr = _fit_text(draw, instr_line, instr_fp, 68, max_w, max_lines=1)
    lh_instr = int(sz_instr * 1.08)

    for line in lines_instr:
        _draw_centered_mixed(draw, y, line, font_instr, CREAM, gold_words,
                             outline_color=(60, 30, 0), outline_w=3, shadow=5)
        y += lh_instr

    # ── Tagline: centered in the bottom dark strip ────────────────────────────
    tag_fp   = bebas
    tag_lines, tag_font, tag_sz = _fit_text(draw, tagline, tag_fp, 52, max_w - PADDING, max_lines=2)
    lh_tag   = int(tag_sz * 1.06)

    # Stack up from the bottom
    total_tag_h = lh_tag * len(tag_lines)
    tag_y = H - total_tag_h - 20

    for line in tag_lines:
        _draw_centered_outlined(draw, tag_y, line, tag_font,
                                fill=WHITE, outline_color=BLACK, outline_w=4, shadow=6)
        tag_y += lh_tag

    img.save(THUMBNAIL_FILE, "JPEG", quality=95)
    print(f"[thumbnail] Saved {THUMBNAIL_FILE} ({os.path.getsize(THUMBNAIL_FILE) // 1024} KB)")
    return THUMBNAIL_FILE


if __name__ == "__main__":
    stub = {
        "raga":             "Darbari Kanada",
        "instrument":       "sitar, bansuri flute & tabla",
        "use_case":         "late night relaxation",
        "thumbnail_hook":   "MIDNIGHT CALM",
        "thumbnail_instr":  "SITAR, BANSURI & TABLA · RAAG DARBARI",
        "thumbnail_tagline":"Saturday Night Deep Relaxation for the Soul",
    }
    run(stub, os.path.join(OUTPUT_DIR, "background.png"))
