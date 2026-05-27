"""
Studio Auto Step — Background Image Generation via Gemini Imagen
Uses brain's image_prompt directly (already has rich Mughal-meets-folk style).
Output: {draft_dir}/background.png  (1920x1080)
"""

import os, sys

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)

from config import IMAGEN_MODEL


def run(client, brain: dict, draft_dir: str) -> str:
    from google.genai import types
    from io import BytesIO
    from PIL import Image

    prompt = brain["image_prompt"]
    print(f"[auto_image] Prompt: {prompt[:80]}...")

    # Brain already specifies rich painterly style — just enforce dimensions
    suffix = " Horizontal landscape 16:9, 1920x1080. No text, no watermarks."

    response = client.models.generate_content(
        model=IMAGEN_MODEL,
        contents=prompt + suffix,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    candidates = response.candidates or []
    if not candidates or not candidates[0].content or not candidates[0].content.parts:
        raise RuntimeError("[auto_image] Gemini returned no image.")

    img_bytes = next(
        (p.inline_data.data for p in candidates[0].content.parts if p.inline_data),
        None,
    )
    if img_bytes is None:
        raise RuntimeError("[auto_image] No inline image data in response.")

    image = Image.open(BytesIO(img_bytes)).resize((1920, 1080), Image.LANCZOS)
    image_path = os.path.join(draft_dir, "background.png")
    image.save(image_path, "PNG")

    size_kb = os.path.getsize(image_path) / 1024
    print(f"[auto_image] Saved {image_path} ({size_kb:.0f} KB)")
    return image_path
