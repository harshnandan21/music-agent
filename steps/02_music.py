"""
Step 2 — Music Generation
Generates 3 Lyria clips, merges them with 3-second crossfade overlap so
the transition is inaudible, trims to exactly 10 minutes, and adds a
2-second fade-in at the start and 5-second fade-out at the end.
Output: output/music.mp3
"""

import os, sys, subprocess, time, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OUTPUT_DIR

MUSIC_FILE      = os.path.join(OUTPUT_DIR, "music.mp3")
TARGET_SEC      = 600   # 10 minutes
CROSSFADE_SEC   = 4     # overlap between clips
FADE_IN_SEC     = 2
FADE_OUT_SEC    = 5
NUM_CLIPS       = 4     # 4 × ~3 min -> ~12 min before trimming, trim to 10


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True
    )
    return float(r.stdout.strip())


def _generate_single_clip(client, prompt: str, index: int) -> str:
    from google.genai import types

    clip_path = os.path.join(OUTPUT_DIR, f"clip_{index}.mp3")
    print(f"[music] Generating clip {index + 1}/{NUM_CLIPS}...")

    for attempt in range(3):
        response = client.models.generate_content(
            model="lyria-3-pro-preview",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["AUDIO"])
        )
        candidates = response.candidates or []
        if candidates and candidates[0].content:
            audio_bytes = next(
                (p.inline_data.data for p in candidates[0].content.parts if p.inline_data is not None),
                None
            )
            if audio_bytes:
                with open(clip_path, "wb") as f:
                    f.write(audio_bytes)
                dur = _get_duration(clip_path)
                size_mb = os.path.getsize(clip_path) / 1_048_576
                print(f"[music] Clip {index + 1}: {dur:.0f}s ({dur/60:.1f} min), {size_mb:.1f} MB")
                return clip_path
        print(f"[music] Clip {index + 1} attempt {attempt + 1} returned no audio, retrying...")
        time.sleep(3)

    raise RuntimeError(f"[music] Failed to generate clip {index + 1} after 3 attempts.")


def _crossfade_merge(clips: list, output_path: str) -> str:
    """
    Merge clips with acrossfade so each transition overlaps by CROSSFADE_SEC.
    Uses qsin (quarter-sine) curve — sounds the most natural for music.
    Chain: [0][1]→[a1], [a1][2]→[out]
    """
    if len(clips) == 1:
        shutil.copy(clips[0], output_path)
        return output_path

    inputs = []
    for clip in clips:
        inputs += ["-i", clip]

    # Build chained acrossfade filter
    filter_parts = []
    prev = "0"
    for i in range(1, len(clips)):
        out_label = "out" if i == len(clips) - 1 else f"a{i}"
        filter_parts.append(
            f"[{prev}][{i}]acrossfade=d={CROSSFADE_SEC}:c1=qsin:c2=qsin[{out_label}]"
        )
        prev = out_label

    filter_complex = "; ".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path,
    ]
    print(f"[music] Crossfade-merging {len(clips)} clips ({CROSSFADE_SEC}s overlap)...")
    subprocess.run(cmd, check=True)
    return output_path


def _trim_and_polish(src: str, dst: str, duration: int) -> str:
    """Trim to exact duration + fade in at start + fade out at end."""
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-t", str(duration),
        "-af", (
            f"afade=t=in:st=0:d={FADE_IN_SEC},"
            f"afade=t=out:st={duration - FADE_OUT_SEC}:d={FADE_OUT_SEC}"
        ),
        "-c:a", "libmp3lame", "-b:a", "192k",
        dst,
    ]
    print(f"[music] Trimming to {duration}s with fade in ({FADE_IN_SEC}s) / fade out ({FADE_OUT_SEC}s)...")
    subprocess.run(cmd, check=True)
    return dst


# ── Main ──────────────────────────────────────────────────────────────────────

def run(client, brain: dict) -> str:
    prompt = brain["music_prompt"]
    print(f"[music] Prompt: {prompt[:80]}...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1 — Generate N clips
    clips = [_generate_single_clip(client, prompt, i) for i in range(NUM_CLIPS)]

    # Step 2 — Crossfade merge
    merged_path = os.path.join(OUTPUT_DIR, "music_merged.mp3")
    _crossfade_merge(clips, merged_path)

    merged_dur = _get_duration(merged_path)
    print(f"[music] Merged: {merged_dur:.0f}s ({merged_dur/60:.1f} min)")

    if merged_dur < TARGET_SEC:
        print(f"[music] Warning: merged audio ({merged_dur:.0f}s) shorter than target ({TARGET_SEC}s)")

    # Step 3 — Trim to 10 min + polish
    actual_target = min(int(merged_dur), TARGET_SEC)
    _trim_and_polish(merged_path, MUSIC_FILE, actual_target)

    # Cleanup temp files
    for clip in clips:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists(merged_path):
        os.remove(merged_path)

    final_dur = _get_duration(MUSIC_FILE)
    size_mb = os.path.getsize(MUSIC_FILE) / 1_048_576
    print(f"[music] Final music: {final_dur:.0f}s ({final_dur/60:.1f} min), {size_mb:.1f} MB -> {MUSIC_FILE}")
    return MUSIC_FILE


if __name__ == "__main__":
    from google import genai as _genai
    _client = _genai.Client(api_key=__import__("config").GEMINI_API_KEY)
    stub = {
        "music_prompt": (
            "Solo sitar playing Raga Yaman Kalyan, romantic, gentle and reflective, "
            "melancholic yet hopeful, slow and deliberate tempo, deeply relaxing, "
            "sustained notes, delicate ornamentation, no lyrics, purely instrumental"
        )
    }
    run(_client, stub)
