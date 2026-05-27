"""
Studio Auto Step — Music Generation via Lyria 3-Pro
Generates 4 Lyria clips, saves them as clip_1.mp3 … clip_4.mp3 in draft_dir.
The caller then passes draft_dir to 02_extend.py to loop/extend to target duration.
"""

import concurrent.futures, os, subprocess, sys, time

STUDIO_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR   = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)

NUM_CLIPS = 4


def _get_duration(path: str) -> float:
    import re
    r = subprocess.run(["ffmpeg", "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"Duration:\s+(\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise RuntimeError(f"[auto_music] Could not read duration of {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def _strip_silence(src: str, dst: str) -> str:
    af = (
        "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-50dB,"
        "areverse,"
        "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-50dB,"
        "areverse"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-af", af, "-c:a", "libmp3lame", "-b:a", "192k", dst],
        check=True, stdin=subprocess.DEVNULL, capture_output=True,
    )
    before = _get_duration(src)
    after  = _get_duration(dst)
    if before - after > 0.5:
        print(f"[auto_music] Stripped {before - after:.1f}s silence from {os.path.basename(src)}")
    return dst


def _generate_clip(client, prompt: str, idx: int, draft_dir: str) -> str:
    from google.genai import types

    raw   = os.path.join(draft_dir, f"_clip_{idx}_raw.mp3")
    clean = os.path.join(draft_dir, f"clip_{idx + 1}.mp3")
    print(f"[auto_music] Generating clip {idx + 1}/{NUM_CLIPS}...")

    for attempt in range(3):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(
                    client.models.generate_content,
                    model="lyria-3-pro-preview",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["AUDIO"]),
                )
                resp = future.result(timeout=300)
        except concurrent.futures.TimeoutError:
            print(f"[auto_music] Clip {idx + 1} attempt {attempt + 1} timed out — retrying...")
            time.sleep(5)
            continue

        candidates = resp.candidates or []
        if candidates and candidates[0].content:
            audio = next(
                (p.inline_data.data for p in candidates[0].content.parts if p.inline_data),
                None,
            )
            if audio:
                with open(raw, "wb") as f:
                    f.write(audio)
                _strip_silence(raw, clean)
                os.remove(raw)
                dur = _get_duration(clean)
                if dur < 60:
                    print(f"[auto_music] Clip {idx + 1} only {dur:.0f}s after stripping — regenerating...")
                    os.remove(clean)
                    time.sleep(3)
                    continue
                print(f"[auto_music] Clip {idx + 1}: {dur:.0f}s ({dur / 60:.1f} min)")
                return clean

        print(f"[auto_music] Clip {idx + 1} attempt {attempt + 1} returned no audio — retrying...")
        time.sleep(3)

    raise RuntimeError(f"[auto_music] Failed to generate clip {idx + 1} after 3 attempts.")


def run(client, brain: dict, draft_dir: str) -> list[str]:
    """Generate NUM_CLIPS Lyria clips into draft_dir. Returns list of clip paths."""
    prompt = brain["music_prompt"]
    print(f"[auto_music] Prompt: {prompt[:80]}...")
    print(f"[auto_music] Generating {NUM_CLIPS} clips into {draft_dir}")

    clips = []
    for i in range(NUM_CLIPS):
        path = _generate_clip(client, prompt, i, draft_dir)
        clips.append(path)

    total = sum(_get_duration(c) for c in clips)
    print(f"[auto_music] All {NUM_CLIPS} clips ready — total raw: {total:.0f}s ({total / 60:.1f} min)")
    return clips
