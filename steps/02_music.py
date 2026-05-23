"""
Step 2 — Music Generation
Generates 4 Lyria clips, strips silence from each clip's boundaries,
merges with crossfade, normalises volume, then trims to exactly 10 minutes
with fade-in and fade-out. Output: output/music.mp3
"""

import os, sys, subprocess, time, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OUTPUT_DIR

MUSIC_FILE      = os.path.join(OUTPUT_DIR, "music.mp3")
TARGET_SEC      = 600   # 10 minutes
CROSSFADE_SEC   = 6     # longer overlap hides any remaining transition bumps
FADE_IN_SEC     = 2
FADE_OUT_SEC    = 5
NUM_CLIPS       = 4     # 4 × ~3 min → ~12 min before trimming


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_duration(path: str) -> float:
    """Parse duration from ffmpeg stderr — works without ffprobe."""
    import re
    r = subprocess.run(["ffmpeg", "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"Duration:\s+(\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise RuntimeError(f"[music] Could not read duration of {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def _strip_silence(src: str, dst: str) -> str:
    """
    Remove leading AND trailing silence from a clip.
    Uses the areverse trick: strip start silence → reverse → strip start silence
    again (which hits the original end) → reverse back.
    Threshold -50dB catches near-silence; 0.5s min avoids clipping musical rests.
    """
    af = (
        "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-50dB,"
        "areverse,"
        "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-50dB,"
        "areverse"
    )
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-af", af,
        "-c:a", "libmp3lame", "-b:a", "192k",
        dst,
    ]
    result = subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True)
    before = _get_duration(src)
    after  = _get_duration(dst)
    stripped = before - after
    if stripped > 0.5:
        print(f"[music] Stripped {stripped:.1f}s of boundary silence from {os.path.basename(src)}")
    return dst


def _generate_single_clip(client, prompt: str, index: int) -> str:
    from google.genai import types

    raw_path    = os.path.join(OUTPUT_DIR, f"clip_{index}_raw.mp3")
    clean_path  = os.path.join(OUTPUT_DIR, f"clip_{index}.mp3")
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
                (p.inline_data.data for p in candidates[0].content.parts
                 if p.inline_data is not None),
                None
            )
            if audio_bytes:
                with open(raw_path, "wb") as f:
                    f.write(audio_bytes)
                dur = _get_duration(raw_path)
                size_mb = os.path.getsize(raw_path) / 1_048_576
                print(f"[music] Clip {index + 1} raw: {dur:.0f}s ({dur/60:.1f} min), {size_mb:.1f} MB")
                # Strip boundary silence before returning
                _strip_silence(raw_path, clean_path)
                os.remove(raw_path)
                return clean_path
        print(f"[music] Clip {index + 1} attempt {attempt + 1} returned no audio, retrying...")
        time.sleep(3)

    raise RuntimeError(f"[music] Failed to generate clip {index + 1} after 3 attempts.")


def _crossfade_merge(clips: list, output_path: str) -> str:
    """
    Merge clips with acrossfade so each transition overlaps by CROSSFADE_SEC.
    Uses qsin (quarter-sine) curve — most natural for music.
    """
    if len(clips) == 1:
        shutil.copy(clips[0], output_path)
        return output_path

    inputs = []
    for clip in clips:
        inputs += ["-i", clip]

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
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
    return output_path


def _trim_and_polish(src: str, dst: str, duration: int) -> str:
    """
    Trim to exact duration + dynamic volume normalisation so there are no
    sudden loud/quiet jumps + fade-in at start + fade-out at end.
    dynaudnorm: frame 500ms, gaussian 31 frames — smooths long-term volume
    without squashing musical dynamics.
    """
    af = (
        "dynaudnorm=f=500:g=31:r=0.9,"
        f"afade=t=in:st=0:d={FADE_IN_SEC},"
        f"afade=t=out:st={duration - FADE_OUT_SEC}:d={FADE_OUT_SEC}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-t", str(duration),
        "-af", af,
        "-c:a", "libmp3lame", "-b:a", "192k",
        dst,
    ]
    print(f"[music] Normalising + trimming to {duration}s "
          f"(fade in {FADE_IN_SEC}s / fade out {FADE_OUT_SEC}s)...")
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
    return dst


# ── Main ──────────────────────────────────────────────────────────────────────

def run(client, brain: dict) -> str:
    prompt = brain["music_prompt"]
    print(f"[music] Prompt: {prompt[:80]}...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1 — Generate clips (silence-stripped)
    clips = [_generate_single_clip(client, prompt, i) for i in range(NUM_CLIPS)]

    # Step 2 — Crossfade merge
    merged_path = os.path.join(OUTPUT_DIR, "music_merged.mp3")
    _crossfade_merge(clips, merged_path)

    merged_dur = _get_duration(merged_path)
    print(f"[music] Merged: {merged_dur:.0f}s ({merged_dur/60:.1f} min)")

    if merged_dur < TARGET_SEC:
        print(f"[music] Warning: merged audio ({merged_dur:.0f}s) shorter than "
              f"target ({TARGET_SEC}s) — adding extra clip")

    # Step 3 — Normalise + trim + fade
    actual_target = min(int(merged_dur), TARGET_SEC)
    _trim_and_polish(merged_path, MUSIC_FILE, actual_target)

    # Cleanup temp files
    for clip in clips:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists(merged_path):
        os.remove(merged_path)

    final_dur = _get_duration(MUSIC_FILE)
    size_mb   = os.path.getsize(MUSIC_FILE) / 1_048_576
    print(f"[music] Final: {final_dur:.0f}s ({final_dur/60:.1f} min), "
          f"{size_mb:.1f} MB → {MUSIC_FILE}")
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
