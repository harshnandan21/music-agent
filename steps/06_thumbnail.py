"""
Step 6 — Thumbnail Generation
Creates a 1280×720 YouTube thumbnail: background image + title text overlay.
Output: output/thumbnail.jpg
"""

import os, sys, textwrap
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OUTPUT_DIR

THUMBNAIL_FILE = os.path.join(OUTPUT_DIR, "thumbnail.jpg")
FONT_PATH_BOLD = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts", "BebasNeue-Regular.ttf")
FONT_PATH_SUB  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts", "Anton-Regular.ttf")


def run(brain: dict, image_path: str) -> str:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    img = Image.open(image_path).convert("RGB").resize((1280, 720), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    title = brain["title"]
    raga  = brain.get("raga", "")
    use_case = brain.get("use_case", "")

    # Dark gradient overlay at bottom
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for y in range(360, 720):
        alpha = int(180 * ((y - 360) / 360))
        ov_draw.rectangle([(0, y), (1280, y + 1)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Load fonts (fallback to default if not present)
    try:
        font_title = ImageFont.truetype(FONT_PATH_BOLD, 72) if os.path.exists(FONT_PATH_BOLD) else ImageFont.load_default()
        font_sub   = ImageFont.truetype(FONT_PATH_SUB,  40) if os.path.exists(FONT_PATH_SUB)  else ImageFont.load_default()
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = ImageFont.load_default()

    # Title (wrap at 28 chars)
    lines = textwrap.wrap(title, width=28)
    y_start = 430
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        w = bbox[2] - bbox[0]
        draw.text(((1280 - w) // 2, y_start), line, font=font_title, fill="white",
                  stroke_width=3, stroke_fill="black")
        y_start += 82

    # Subtitle tag (raga + use case)
    subtitle = f"Raga {raga} · {use_case.title()}"
    bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sw = bbox[2] - bbox[0]
    draw.text(((1280 - sw) // 2, y_start + 10), subtitle, font=font_sub,
              fill="#FFD700", stroke_width=2, stroke_fill="black")

    img.save(THUMBNAIL_FILE, "JPEG", quality=95)
    size_kb = os.path.getsize(THUMBNAIL_FILE) / 1024
    print(f"[thumbnail] Saved {THUMBNAIL_FILE} ({size_kb:.0f} KB)")
    return THUMBNAIL_FILE


if __name__ == "__main__":
    stub = {
        "title": "Need Deep Rest? Raga Yaman on Sitar | 12 Min Indian Classical",
        "raga": "Yaman",
        "use_case": "deep sleep",
    }
    run(stub, os.path.join(OUTPUT_DIR, "background.png"))
