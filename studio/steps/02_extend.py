"""
Studio Step 2 — Extend
Takes 1 or 2 user-provided music clips from the draft folder and extends them to ~20 min.

With 1 clip  : loops as clip_1 → clip_1 → clip_1 → ... until 20 min
With 2 clips : interleaves as clip_1 → clip_2 → clip_1 → clip_2 → ... until 20 min

Crossfade 6s between every segment (qsin curve — natural for Indian classical).
Final pass: dynaudnorm volume levelling + 3s fade-in + 8s fade-out.
Output: draft_dir/music.mp3
"""

import os, shutil, subprocess, sys, tempfile

STUDIO_DIR   = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR     = os.path.dirname(STUDIO_DIR)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, STUDIO_DIR)

from utils import get_duration

DEFAULT_MIN  = 20
CROSSFADE_SEC = 6
FADE_IN_SEC  = 3
FADE_OUT_SEC = 8



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
    return dst


def _crossfade_merge(clips: list, output_path: str) -> str:
    """Merge clips with acrossfade, chaining pairs to avoid huge filter_complex strings."""
    if len(clips) == 1:
        shutil.copy(clips[0], output_path)
        return output_path

    print(f"[extend] Crossfade-merging {len(clips)} segments ({CROSSFADE_SEC}s overlap)...")
    tmp_files = []
    current = clips[0]

    for i, next_clip in enumerate(clips[1:], 1):
        is_last = (i == len(clips) - 1)
        if is_last:
            out = output_path
        else:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False,
                dir=os.path.dirname(output_path),
            )
            tmp.close()
            out = tmp.name
            tmp_files.append(out)

        subprocess.run([
            "ffmpeg", "-y", "-i", current, "-i", next_clip,
            "-filter_complex",
            f"[0][1]acrossfade=d={CROSSFADE_SEC}:c1=qsin:c2=qsin[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", out,
        ], check=True, stdin=subprocess.DEVNULL, capture_output=True)
        current = out

    for f in tmp_files:
        if os.path.exists(f):
            os.remove(f)

    return output_path


def _normalise_and_fade(src: str, dst: str, duration: float) -> str:
    af = (
        "dynaudnorm=f=500:g=31:r=0.9,"
        f"afade=t=in:st=0:d={FADE_IN_SEC},"
        f"afade=t=out:st={duration - FADE_OUT_SEC}:d={FADE_OUT_SEC}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-af", af,
        "-c:a", "libmp3lame", "-b:a", "192k",
        dst,
    ]
    print(f"[extend] Normalising + fading ({duration:.0f}s)...")
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
    return dst


def run(draft_dir: str, target_min: int = DEFAULT_MIN) -> str:
    # Discover user clips — any .mp3 or .wav in the folder, sorted by name
    TARGET_SEC = target_min * 60
    print(f"[extend] Target duration: {target_min} min ({TARGET_SEC}s)")

    SKIP = {"music.mp3"}
    clips_raw = sorted([
        os.path.join(draft_dir, f)
        for f in os.listdir(draft_dir)
        if f.lower().endswith((".mp3", ".wav")) and f not in SKIP
    ])

    if not clips_raw:
        raise FileNotFoundError(
            f"[extend] No audio files found in {draft_dir}. "
            "Drop your .mp3 or .wav file(s) there and re-run --publish."
        )

    print(f"[extend] Found {len(clips_raw)} user clip(s): {[os.path.basename(c) for c in clips_raw]}")

    # Strip silence from each source clip once
    stripped = []
    for i, src in enumerate(clips_raw):
        dst = os.path.join(draft_dir, f"_stripped_{i+1}.mp3")
        _strip_silence(src, dst)
        dur = get_duration(dst)
        print(f"[extend] Clip {i+1} after silence strip: {dur:.0f}s ({dur/60:.1f} min)")
        stripped.append(dst)

    # Build interleaved sequence until we exceed TARGET_SEC
    # With 2 clips: 1→2→1→2→... ; with 1 clip: 1→1→1→...
    # Each crossfade overlap reduces effective duration by CROSSFADE_SEC
    sequence = []
    total = 0.0
    idx = 0
    while total < TARGET_SEC + 60:   # overshoot by 1 min so trim is clean
        clip = stripped[idx % len(stripped)]
        sequence.append(clip)
        dur = get_duration(clip)
        # Each segment after the first loses CROSSFADE_SEC to overlap
        if len(sequence) == 1:
            total += dur
        else:
            total += dur - CROSSFADE_SEC
        idx += 1
        if len(sequence) > 50:   # safety cap
            break

    print(f"[extend] Built sequence of {len(sequence)} segments, est. {total:.0f}s ({total/60:.1f} min)")

    merged_path = os.path.join(draft_dir, "_merged.mp3")
    _crossfade_merge(sequence, merged_path)

    merged_dur = get_duration(merged_path)
    print(f"[extend] Merged: {merged_dur:.0f}s ({merged_dur/60:.1f} min)")

    out_path = os.path.join(draft_dir, "music.mp3")
    _normalise_and_fade(merged_path, out_path, merged_dur)

    # Cleanup temp files
    for p in stripped + [merged_path]:
        if os.path.exists(p):
            os.remove(p)

    final_dur = get_duration(out_path)
    size_mb   = os.path.getsize(out_path) / 1_048_576
    print(f"[extend] Done: {final_dur:.0f}s ({final_dur/60:.1f} min), {size_mb:.1f} MB -> {out_path}")
    return out_path
