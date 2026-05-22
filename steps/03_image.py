"""
Step 3 — Image Generation
Generates a background image via Gemini Imagen (same model/pattern as affirmation agent).
Output: output/background.png (16:9 landscape)
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import IMAGEN_MODEL, OUTPUT_DIR

IMAGE_FILE = os.path.join(OUTPUT_DIR, "background.png")


def run(client, brain: dict) -> str:
    from google.genai import types
    from io import BytesIO
    from PIL import Image

    prompt = brain["image_prompt"]
    print(f"[image] Generating: {prompt[:80]}...")

    # Same pattern as affirmation agent's _generate_raw_background
    response = client.models.generate_content(
        model=IMAGEN_MODEL,
        contents=prompt + " Horizontal landscape 16:9. Photorealistic, cinematic, 4K. No text, no watermark, no people.",
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
    )

    candidates = response.candidates or []
    if not candidates or not candidates[0].content or not candidates[0].content.parts:
        raise RuntimeError(f"[image] Gemini returned no image for prompt: {prompt[:60]}")

    img_bytes = next(
        (part.inline_data.data for part in candidates[0].content.parts if part.inline_data is not None),
        None
    )
    if img_bytes is None:
        raise RuntimeError("[image] No inline image data in response.")

    image = Image.open(BytesIO(img_bytes)).resize((1920, 1080), Image.LANCZOS)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    image.save(IMAGE_FILE, "PNG")

    size_kb = os.path.getsize(IMAGE_FILE) / 1024
    print(f"[image] Saved {IMAGE_FILE} ({size_kb:.0f} KB)")
    return IMAGE_FILE


if __name__ == "__main__":
    from google import genai as _genai
    _client = _genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    stub = {
        "image_prompt": (
            "Mughal miniature painting style, Indian classical musician playing sitar "
            "in a palace courtyard at dusk, deep indigo and gold color palette, "
            "peacocks in foreground, intricate geometric mandala patterns, oil lamp light, no text"
        )
    }
    run(_client, stub)
