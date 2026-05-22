"""
Step 1 — Brain
Uses Gemini Flash to generate all prompts, metadata, and titles for today's video.
Returns a dict that flows through the rest of the pipeline.
"""

import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    BRAIN_MODEL,
    RAGAS, INSTRUMENTS, USE_CASES, VISUAL_STYLES,
    today_index,
)


def run(client) -> dict:
    idx = today_index()

    raga       = RAGAS[idx % len(RAGAS)]
    instrument = INSTRUMENTS[idx % len(INSTRUMENTS)]
    use_case   = USE_CASES[idx % len(USE_CASES)]
    style      = VISUAL_STYLES[idx % len(VISUAL_STYLES)]

    prompt = f"""You are a creative director for an Indian classical music YouTube channel.
Today's rotation:
- Raga: {raga['raga']} ({raga['mood']})
- Instrument: {instrument}
- Use case: {use_case}
- Visual style: {style}

Return a JSON object (no markdown, no extra text) with exactly these keys:
{{
  "title": "Pain-point question title ≤ 60 chars, e.g. Need Deep Rest? Raga Yaman on Sitar | 12 Min Indian Classical",
  "description": "YouTube description 150-200 words, include raga name, use case benefits, relevant hashtags",
  "tags": ["list", "of", "10", "youtube", "tags"],
  "music_prompt": "Detailed prompt for Lyria music model: instrument, raga feel, tempo, mood, no lyrics, instrumental only",
  "image_prompt": "Detailed prompt for Imagen: visual style ({style}), scene, colors, lighting, no text in image",
  "video_prompt": "Short prompt for Veo to animate the image: gentle camera movement, 8-second seamless loop",
  "raga": "{raga['raga']}",
  "instrument": "{instrument}",
  "use_case": "{use_case}",
  "visual_style": "{style}"
}}"""

    response = client.models.generate_content(model=BRAIN_MODEL, contents=prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text.strip())
    print(f"[brain] Raga={data['raga']} | Instrument={data['instrument']} | Style={data['visual_style']}")
    print(f"[brain] Title: {data['title']}")
    return data


if __name__ == "__main__":
    import pprint
    from google import genai as _genai
    _client = _genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    pprint.pprint(run(_client))
