# DhunDetox Music Agent — Implementation Summary

**Channel:** DhunDetox (YouTube)  
**Purpose:** Daily Indian classical music videos for mental wellness (stress, sleep, focus, anxiety) — fully automated from idea to published video.  
**Stack:** Python · Google Gemini · FFmpeg · Telegram Bot · YouTube Data API v3

---

## Architecture Overview

The system has two layers:

**Root layer** (`steps/`, `orchestrator.py`) — original pipeline, AI-generated music via Lyria + AI images via Imagen. Mostly replaced by the Studio layer for day-to-day use.

**Studio layer** (`studio/`) — manual hybrid workflow. Gemini generates the idea/metadata; the user creates music on Suno and images on Gemini Pro; the pipeline extends, assembles, and uploads.

```
Daily flow:

[9 AM cron]
    │
    └─► 01_brain.py (Gemini 2.5 Flash)
            │  raga, title, description, keywords, image/music/video prompts
            ▼
    studio/steps/01_draft.py
            │  saves brain.json → sends Telegram (APPROVE/REJECT + prompts .txt)
            │  waits 10h → auto-reject on timeout
            ▼
    [User creates on phone]
            │  Suno (music) + Gemini Pro (background + thumbnail)
            │  drops files into studio/drafts/YYYY-MM-DD/
            ▼
    python studio/orchestrator.py --publish
            │
            ├─► 02_extend.py  — extends clips to 20+ min (crossfade loop)
            ├─► 03_assemble.py — assembles video (clip loop OR static image)
            │   [Telegram: APPROVE / REJECT preview]
            │   [Telegram: schedule buttons]
            └─► 04_upload.py  — uploads to YouTube + sets thumbnail + playlist
                    [Telegram: upload confirmation photo]
```

---

## File Structure

```
music-agent/
├── config.py                    # Weekly schedule, content seeds, API keys, models
├── steps/
│   ├── 01_brain.py              # Gemini idea generator (title, description, prompts)
│   └── 07_upload.py             # YouTube upload (OAuth, video, thumbnail, playlist)
├── studio/
│   ├── orchestrator.py          # Two-phase entrypoint: --draft / --publish / --cleanup
│   ├── telegram.py              # Telegram Bot helpers
│   ├── utils.py                 # Shared: get_duration() via ffmpeg
│   └── steps/
│       ├── 01_draft.py          # Run brain + send Telegram prompts + wait for approval
│       ├── 02_extend.py         # Extend music clips to 20 min
│       ├── 03_assemble.py       # Assemble final video (clip loop or static image)
│       └── 04_upload.py         # Thin wrapper → calls steps/07_upload.py
```

---

## Module Details

### `config.py`

Single source of truth for the entire pipeline.

- **`WEEKLY_SCHEDULE`** — 7-day dict (Monday=0 … Sunday=6). Each entry has: `raga`, `raga_mood`, `instruments`, `use_case`, `theme`, `music_hints`, `image_hints`, and optional overrides (`hz_frequency`, `title`, `thumbnail_hook`, `thumbnail_instr`, `thumbnail_tagline`, `playlist`). Locked fields are passed to Gemini as hard constraints and force-merged into output — Gemini cannot change them.
- **`CONTENT_SEEDS`** — outcome hooks, atmosphere hooks, title patterns, hook phrases, hashtag tiers, avoid-generic list — all injected into the brain prompt.
- **`MADHUBANI_STYLE`** — shared visual style spec (Mithila folk painting, 16:9, natural pigments, no photorealism).
- **`VIDEO_ANIMATION_GUIDE`** — per-scene animation percentages for Veo video prompt guidance.
- **`YOUTUBE_KEYWORDS`** — English + Hinglish keyword banks for tag generation.
- **`PLAYLISTS`** — 5 themed playlists (morning, focus, stress, sleep, midnight). IDs loaded from `.env` env vars at runtime.
- **`FFMPEG_DIR`** — injects Shotcut's ffmpeg into PATH so all subprocess calls resolve.
- **Models:** `BRAIN_MODEL = gemini-2.5-flash`, `MUSIC_MODEL = lyria-realtime-exp`, `IMAGEN_MODEL = gemini-3-pro-image-preview`

---

### `steps/01_brain.py`

Calls Gemini 2.5 Flash to generate all post metadata.

**What Gemini writes:** title (if not locked), description, keywords, tags, music_prompt, image_prompt, video_prompt, hook_angle, hook_phrase, thumbnail_hook, thumbnail_tagline.

**Hard constraints:** any field set in `WEEKLY_SCHEDULE` is passed in a `LOCKED VALUES` section and then force-merged into the output via `data.update(locked)` — Gemini cannot override them.

**Description template (11 sections, plain text — no Markdown):**
1. Emoji + SEO title repeat
2. 2-3 sentence hook (pain point, punchy)
3. Raga + Hz benefit + instrument paragraph
4. Hook phrase (quoted)
5. Cultural/historical context of the raga
6. PERFECT FOR: 8 bullet points
7. WHY RAAG X HEALS: parasympathetic + Hz science
8. HOW TO USE: 8-step numbered list
9. Hindi section (3-4 lines + translated hook phrase)
10. CTA (like, subscribe, comment question, save)
11. Disclaimer + 15 hashtags

**Keyword string:** 470-480 chars, comma-separated, no spaces after commas. Pattern: raga variations → instrument+raga combos → instrument alone → meditation/healing terms → emotion terms → `thelifemerit` (channel name) → Hindi keywords at end. No Hz frequency terms.

**Tags:** 15 max, English only, each ≤30 chars, total <400 chars combined.

**Validation:** prints a warning if keyword string is outside 470-480 chars.

**Anti-repeat tracking:** last 20 published ideas loaded from `used_ideas.json`; titles + dates injected into prompt so Gemini avoids repeated angles.

---

### `steps/07_upload.py`

Uploads to YouTube via Data API v3 with OAuth 2.0.

**Key behaviours:**
- Parses the full `keywords` string (not the 15-item `tags` array) to build YouTube tags — filters non-ASCII, drops tags >30 chars, stops at 500-char YouTube limit.
- Strips Markdown from description: removes `*`/`**`, replaces `---` with `────────────────────────────`.
- Scheduling: if `publish_at` (RFC3339 IST string) is passed → `privacyStatus: private` + `publishAt`; otherwise → `public`.
- Thumbnail: PIL JPEG compression loop (quality 85 → 70 → 55 → 40) to stay under YouTube's 2MB limit.
- Playlist: looks up playlist ID by key from `brain["playlist"]` → calls `playlistItems().insert()`.

---

### `studio/telegram.py`

All Telegram Bot interactions via `requests` (long-polling, no webhook).

| Function | Purpose |
|---|---|
| `send_text(text)` | Plain text message (HTML parse mode) |
| `send_document(filename, content, caption)` | Send `.txt` file — user opens on phone to copy-paste prompts |
| `send_photo(image_path, caption)` | Photo with caption, no buttons |
| `send_approval(image_path, caption, token)` | Photo (or text) + APPROVE / REJECT inline buttons |
| `wait_for_decision(token, timeout)` | Long-poll until button tapped. Returns `approved`/`rejected`/`timeout` |
| `send_schedule_prompt(token)` | Schedule buttons: 1 min / 5 min / 30 min / 1 hour (relative from now) + Publish Now |
| `wait_for_schedule(token, timeout=10800)` | Poll for schedule tap. Returns RFC3339 IST string (now + chosen offset) or `None` (publish now). 3h timeout → publish now |
| `new_token()` | UUID hex (10 chars) — unique per approval/schedule session |

**Callback data formats:**
- Approval: `APPROVE_{token}` / `REJECT_{token}`
- Schedule: `SCH_{token}_{day_offset}_{hour}` or `PUB_NOW_{token}`

**Image compression:** `_compress_for_telegram()` loops quality (85→70→55→40) until <9MB; last resort halves dimensions.

---

### `studio/steps/01_draft.py`

Phase 1 of the studio workflow.

1. Runs `steps/01_brain.py` via `importlib.util` (handles digit-prefixed module names).
2. Saves `brain.json` to `studio/drafts/YYYY-MM-DD/`.
3. Sends Telegram approval message with idea summary.
4. Sends a `.txt` document with all three prompts bundled (easy copy-paste on phone):
   - **Suno Custom Mode:** style field (raga, instruments, BPM, time_tag, no vocals) + structural lyrics markers (Alap → Vilambit Gat → Extended Meditation → Fade)
   - **Gemini Pro — Background Image:** wraps `brain["image_prompt"]` from Gemini
   - **Gemini Pro — Thumbnail:** Madhubani 60/40 composition (instrument dead-centre, clear text space right), mood + hook/tagline overlay notes
5. Waits 10 hours for APPROVE tap. Timeout → auto-rejected.
6. On approval: sends drop-file instructions with exact filenames.

---

### `studio/steps/02_extend.py`

Extends 1 or 2 user-provided clips to 20+ minutes.

**Algorithm:**
1. Auto-discovers `.mp3`/`.wav` files in the draft folder (sorted by name, skips `music.mp3`).
2. Strips silence from each clip (both ends, -50dB threshold).
3. Builds an interleaved sequence (1 clip: `1→1→1…`, 2 clips: `1→2→1→2…`) until ≥21 minutes.
4. Crossfade-merges segments **iteratively** (pair-wise, not one giant filter) — 6s `acrossfade` with `qsin` curve (natural for Indian classical).
5. Final pass: `dynaudnorm` volume levelling + 3s fade-in + 8s fade-out.
6. Output: `draft_dir/music.mp3`

**Why iterative merge:** A single `filter_complex` with 50 inputs would exceed FFmpeg's filter graph limits and produce huge commands. Pair-wise chaining avoids this.

---

### `studio/steps/03_assemble.py`

Assembles the final `video.mp4`. Two modes:

**Video clip mode (preferred)** — triggered when `clip.mp4` exists in the draft folder:
1. `_make_loop_unit()` — bakes a 0.5s cross-dissolve at the loop point:
   - Feeds the same clip to both FFmpeg inputs
   - `xfade=transition=fade:duration=0.5:offset={dur-0.5}` blends the clip's end into its own beginning
   - Trims output to `dur - 0.5s` so the dissolve is pre-baked into the unit
   - Result: when stream_loop repeats the unit, clip[0] picks up seamlessly — no visible seam
2. `_assemble_from_clip()` — uses `-stream_loop -1` on the loop unit + audio + scale/pad to 1920×1080 + 2s fade-in + 3s fade-out

**Static image mode (fallback)** — triggered when no `clip.mp4`:
- Auto-discovers `background.png/jpg` (skips `thumbnail.png/jpg`)
- `-loop 1` on the image + audio + same scale/pad/fade filters

**Both modes produce:** 1920×1080, H.264, AAC 192k, `+faststart`, duration matches audio exactly.

---

### `studio/steps/04_upload.py`

Thin wrapper: finds `video.mp4` + best available thumbnail → calls `steps/07_upload.py`.  
Passes `publish_at` through for scheduled publishing.

---

### `studio/orchestrator.py`

Two-phase entrypoint with three commands:

**`--draft`**
- Guards against overwriting: skips if `brain.json` exists unless `--force` passed.
- Retry loop: up to 3 attempts on rejection; sends "Generating fresh idea..." between retries.
- `--date YYYY-MM-DD` to draft for a specific date.

**`--publish`**
- Sends Telegram progress updates at each step.
- Skip guards: skips extend if `music.mp3` exists; skips assemble if `video.mp4` is non-empty.
- Corrupt video guard: if `video.mp4` exists but is 0 bytes → deletes and re-assembles.
- After assembly: sends Telegram approval (preview image + metadata) with 6h timeout.
- After approval: sends schedule prompt with tap buttons; 3h timeout → publish now.
- After upload: sends Telegram confirmation photo with "Scheduled for…" or "Live now" label.
- `--date YYYY-MM-DD` to publish a specific draft.

**`--cleanup [--days N]`** (default 30 days)
- Deletes `studio/drafts/YYYY-MM-DD/` folders older than N days.

---

### `studio/utils.py`

```python
def get_duration(path: str) -> float:
    # Runs ffmpeg -i, parses "Duration: HH:MM:SS.ms" from stderr
```

Shared by `02_extend.py` and `03_assemble.py`.

---

## Weekly Content Schedule

| Day | Raga | Instruments | Use Case | Hz | Playlist |
|---|---|---|---|---|---|
| Monday | Chandrakauns | Veena & Tabla | Study & focus | 741Hz | focus |
| Tuesday | Yaman Kalyan | Sitar & Bansuri | Evening cortisol drop | 174Hz | stress |
| Wednesday | Bageshri | Bansuri | Overthinking & anxiety | 528Hz | stress |
| Thursday | Yaman | Santoor & Tanpura | Deep sleep | 432Hz | sleep |
| Friday | Bhupali | Sitar, Sarod & Tabla | Morning prana | 432Hz | morning |
| Saturday | Darbari Kanada | Sitar, Bansuri & Tabla | Overactive mind / late night | 396Hz | midnight |
| Sunday | Bhairavi | Bansuri & Tanpura | Morning cortisol reset | 432Hz | morning |

---

## YouTube Playlists

| Key | Playlist Name |
|---|---|
| `morning` | Morning Raga Rituals |
| `focus` | Focus & Brain Clarity |
| `stress` | Stress & Overthinking Relief |
| `sleep` | Sleep & Deep Rest |
| `midnight` | Midnight Calm |

Playlist IDs live in `.env` as `YT_PLAYLIST_MORNING`, `YT_PLAYLIST_FOCUS`, etc.

---

## Drop Files Reference

Before running `--publish`, drop into `studio/drafts/YYYY-MM-DD/`:

| File | Required | Notes |
|---|---|---|
| `clip_1.mp3` | Yes | Primary Suno-generated music clip |
| `clip_2.mp3` | No | Second variation — interleaved with clip_1 |
| `clip.mp4` | No | 8-second Veo loop — preferred over background image |
| `background.png` | If no clip.mp4 | 1920×1080 Madhubani background (Gemini Pro) |
| `thumbnail.png` | No | High-contrast thumbnail (Gemini Pro, 16:9) |

---

## Environment Variables (`.env`)

```
GEMINI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
YOUTUBE_CLIENT_SECRET_FILE=client_secret.json
YOUTUBE_TOKEN_FILE=youtube_token.json
YT_PLAYLIST_MORNING=PLxxxxxxx
YT_PLAYLIST_FOCUS=PLxxxxxxx
YT_PLAYLIST_STRESS=PLxxxxxxx
YT_PLAYLIST_SLEEP=PLxxxxxxx
YT_PLAYLIST_MIDNIGHT=PLxxxxxxx
```

---

## Key Design Decisions

**Plain text descriptions** — YouTube renders `**bold**` and `---` as literal characters. All Markdown was removed from the brain prompt template and a safety strip (`re.sub`) was added in the upload step.

**Keywords string over tags array** — The `keywords` string (~475 chars) contains more terms than the 15-item `tags` array. Upload now parses the full keywords string to maximise YouTube discoverability.

**Cross-dissolve baked into loop unit** — Simply looping an 8-second clip creates a visible cut at the repeat point. The dissolve is pre-baked into the loop unit (last 0.5s blends into first 0.5s), so `stream_loop -1` produces a seamless 20-minute video.

**Iterative pair-wise crossfade merge** — A single FFmpeg `filter_complex` with 50 audio inputs would exceed graph size limits. Sequential pair-wise merging keeps each FFmpeg call small and reliable.

**Telegram .txt document for prompts** — Sending prompts as a `<pre>` block was hard to copy on mobile. Sending as a `.txt` file attachment lets the user tap → open in any text editor → select all.

**Schedule tap buttons** — Typing `2026-05-25 21:00` on a phone is error-prone. Relative delay buttons (1 min / 5 min / 30 min / 1 hour / Publish Now) work regardless of time zone or what time of day the upload happens. The chosen offset is added to `datetime.now(IST)` at tap time, so the scheduled publish time is always accurate.

**Force-merge locked config** — `data.update(locked)` runs after Gemini's JSON is parsed, so schedule overrides always win even if Gemini hallucinates a different value.

**Draft overwrite guard** — Re-running `--draft` on a day that already has `brain.json` silently skips unless `--force` is passed, preventing accidental idea replacement.

**Corrupt video guard** — FFmpeg can crash mid-write, leaving a 0-byte `video.mp4`. The orchestrator checks `os.path.getsize(video_path) > 0` and re-assembles if needed.

---

## Usage Commands

```bash
# Generate today's idea (sends to Telegram for approval)
python studio/orchestrator.py --draft

# Generate idea for a specific date
python studio/orchestrator.py --draft --date 2026-05-27

# Force-regenerate even if brain.json exists
python studio/orchestrator.py --draft --force

# Publish today's draft (after dropping files)
python studio/orchestrator.py --publish

# Publish a specific date's draft
python studio/orchestrator.py --publish --date 2026-05-25

# Delete draft folders older than 30 days
python studio/orchestrator.py --cleanup

# Delete draft folders older than 14 days
python studio/orchestrator.py --cleanup --days 14
```
