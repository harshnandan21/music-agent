"""One-shot: generate description+tags for today's video and push to YouTube."""
import sys, os, json, importlib.util
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv; load_dotenv()
from google import genai
from googleapiclient.discovery import build

VIDEO_ID = "7YQzLVNi100"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """Write a YouTube description and tags for this Indian classical music video.

Title: 396Hz Sitar, Flute, Tabla for Late Night Anxiety Reset | Darbari Kanada
Raga: Darbari Kanada — majestic, contemplative, late-night gravity
Instruments: Sitar, Bansuri Flute, Tabla
Use case: Late night relaxation, anxiety relief
Hz: 396Hz
Hook: You don't need to be okay right now. Just be here.
Channel: DhunDetox — Indian classical music for mental wellness, urban professionals 25-40yo

DESCRIPTION GUIDELINES:
- Open with the hook (2 punchy sentences)
- English section: raga name, instruments, use case benefits, DhunDetox brand voice
- Bullet list of 8-10 use cases (meditation, sleep, yoga, study, anxiety, etc.)
- 2-3 sentences on why Raga Darbari Kanada heals
- Short Hindi section (3-4 lines summarising the video)
- Close with: Like · Save · Share if this helped someone you know
- End with exactly 15 hashtags: mix of big (#meditationmusic #indianclassicalmusic #healingmusic #stressrelief #sleepmusic) medium (#sitarmusic #bansuriflute #ragamusic #soundhealing #indianambient) niche (#ragatherapy #dhundetox #darbari) hindi (#तनावमुक्ति #मनशांति)
- Total 250+ words

TAGS GUIDELINES: 40 tags mixing raga name, instrument names, use case terms, English + Hindi/Hinglish search terms

Return pure JSON only — no markdown, no extra text:
{
  "description": "...",
  "tags": ["...", "..."]
}"""

print("Calling Gemini for description + tags...")
resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
text = resp.text.strip()
if text.startswith("```"):
    text = text.split("```")[1]
    if text.startswith("json"):
        text = text[4:]
data = json.loads(text.strip())
import re
safe_tags = []
seen = set()
total_len = 0
for t in data["tags"]:
    # Keep only a-z A-Z 0-9 and spaces; strip and collapse whitespace
    t = re.sub(r'[^a-zA-Z0-9 ]', '', t).strip()
    t = re.sub(r' +', ' ', t)
    if not t or len(t) > 30:
        continue
    tl = t.lower()
    if tl in seen:
        continue
    if total_len + len(t) + 1 > 490:
        break
    safe_tags.append(t)
    seen.add(tl)
    total_len += len(t) + 1
data["tags"] = safe_tags
print(f"Description: {len(data['description'])} chars | Tags: {len(safe_tags)} total_len={total_len}")
print("Tags:", safe_tags)

# Update YouTube video metadata
spec = importlib.util.spec_from_file_location("upload", os.path.join("steps", "07_upload.py"))
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)

creds = upload._get_credentials()
youtube = build("youtube", "v3", credentials=creds)

# Strip description to ASCII only (YouTube rejects Devanagari in some fields)
import unicodedata
desc_ascii = data["description"].encode("ascii", "ignore").decode("ascii")

youtube.videos().update(
    part="snippet",
    body={
        "id": VIDEO_ID,
        "snippet": {
            "title":           "396Hz Sitar, Flute, Tabla for Late Night Anxiety Reset | Darbari Kanada",
            "description":     desc_ascii,
            "tags":            ["sitar", "meditation music", "indian classical music", "stress relief", "sleep music", "raga darbari kanada", "396hz", "healing music", "bansuri flute", "tabla music", "DhunDetox", "anxiety relief", "deep relaxation", "sound healing", "hindustani classical"],
            "categoryId":      "10",
            "defaultLanguage": "en",
        }
    }
).execute()
print(f"YouTube video {VIDEO_ID} updated with description and tags.")

# Persist to used_ideas.json
ideas_file = os.path.join(os.path.dirname(__file__), "used_ideas.json")
with open(ideas_file) as f:
    ideas = json.load(f)
ideas[-1]["description"] = data["description"]
ideas[-1]["tags"] = data["tags"]
with open(ideas_file, "w") as f:
    json.dump(ideas, f, indent=2)
print("used_ideas.json updated.")
