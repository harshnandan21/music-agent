# DhunDetox Music Agent — Implementation Summary

**Channel:** DhunDetox (YouTube)  
**Purpose:** Daily Indian classical music videos for mental wellness (stress, sleep, focus, anxiety) — fully automated from idea to published video.  
**Stack:** Python · Google Gemini · FFmpeg · Telegram Bot · YouTube Data API v3

---

## Architecture Overview

The system has two layers:

**Root layer** (`steps/`, `orchestrator.py`) — original pipeline, AI-generated music via Lyria + AI images via Imagen. Mostly replaced by the Studio layer for day-to-day use.

**Studio layer** (`studio/`) — unified AUTO + MANUAL workflow. Gemini generates the idea/metadata; content is either AI-generated (AUTO) or user-provided via Suno/Gemini Pro (MANUAL); the pipeline extends, assembles, and uploads.

```
Daily flow:

[8 AM cron / manual --draft]
    │
    └─► 01_draft.py (Gemini 2.5 Flash)
            │  raga, title, description, keywords, image/music/video prompts
            │  sends Telegram: APPROVE / REJECT
            ▼
    [User approves on Telegram]
            │
            ├─► AUTO mode
            │       │  Lyria generates music clips
            │       │  Gemini generates background image
            │       │  extend → assemble → upload
            │
            └─► MANUAL mode
                    │
                    ├─► 📱 Telegram files
                    │       │  User sends .mp3 + image via Telegram
                    │       │  Bot downloads, extend → assemble → upload
                    │
                    └─► 💻 Laptop drop
                            │  Drop files in studio/drafts/YYYY-MM-DD/
                            └─► python studio/orchestrator.py --publish
```

---

## File Structure

```
music-agent/
├── config.py                    # Weekly schedule, content seeds, API keys, models
├── startup.py                   # Hetzner/Railway entry: decode base64 tokens → run --draft
├── setup.sh                     # One-command Hetzner server setup
├── deploy.sh                    # Re-deploy: git pull + pip update
├── railway.toml                 # Railway cron config (2:30 AM UTC = 8 AM IST)
├── nixpacks.toml                # Railway build config (ffmpeg + python312)
├── assets/
│   └── logo.png                 # DhunDetox circular brand logo (stamped on every video)
├── steps/
│   ├── 01_brain.py              # Gemini idea generator (title, description, prompts)
│   └── 07_upload.py             # YouTube upload (OAuth, video, thumbnail, playlist, tags)
├── studio/
│   ├── orchestrator.py          # Unified entrypoint: --draft / --publish / --cleanup
│   ├── telegram.py              # Telegram Bot helpers (approval, schedule, file receiver)
│   ├── utils.py                 # Shared: get_duration() via ffmpeg
│   └── steps/
│       ├── 01_draft.py          # Run brain + send Telegram prompts + wait for approval
│       ├── 02_extend.py         # Extend music clips to target duration
│       ├── 03_assemble.py       # Assemble final video + stamp brand logo
│       ├── 04_upload.py         # Thin wrapper → calls steps/07_upload.py
│       ├── auto_music.py        # AUTO: generate Lyria clips
│       └── auto_image.py        # AUTO: generate Gemini background image
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
- **`FFMPEG_DIR`** — injects Shotcut's ffmpeg into PATH on Windows only (`os.name == "nt"`).
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

**Keyword string:** 470-480 chars, comma-separated, no spaces after commas. Pattern: raga variations → instrument+raga combos → instrument alone → meditation/healing terms → emotion terms → channel name → Hindi keywords at end.

**Tags:** built from curated `tags[]` first, then keywords string fills remaining budget. Total budget: 470 chars. No per-tag character limit. English-only (ASCII filter).

**Anti-repeat tracking:** last 20 published ideas loaded from `used_ideas.json`; titles + dates injected into prompt so Gemini avoids repeated angles.

---

### `steps/07_upload.py`

Uploads to YouTube via Data API v3 with OAuth 2.0.

**Tag building logic:**
1. Start with curated `tags[]` array (priority, best terms)
2. Fill remaining budget from `keywords` string
3. ASCII filter (no Hindi tags — YouTube rejects them)
4. Total budget: 470 chars (YouTube limit is 500 — 30-char safety margin)
5. No per-tag length limit

**Key behaviours:**
- Network retry: 5 attempts with exponential backoff (5s, 10s, 20s, 40s, 80s) on `ConnectionResetError` during large file upload.
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
| `send_duration_prompt(token)` | Duration buttons: 1/20/30/60 min + Custom |
| `wait_for_duration(token, timeout=600)` | Poll for duration tap or typed number. Default 20 min on timeout |
| `send_schedule_prompt(token)` | Schedule buttons: today at 9AM/12PM/6PM/9PM, tomorrow 9AM + Custom + Publish Now |
| `wait_for_schedule(token, timeout=10800)` | Poll for schedule tap. Returns RFC3339 IST string or `None`. 3h timeout → publish now |
| `send_choice_prompt(token, text, options)` | Generic inline keyboard with (label, code) pairs |
| `wait_for_choice(token, timeout=3600)` | Poll for choice tap. Returns code string or None |
| `wait_for_audio_file(draft_dir, timeout=86400)` | Poll for audio/document message, download, save as `clip_1.<ext>`. Returns path or None |
| `wait_for_image_file(draft_dir, timeout=86400)` | Poll for photo/image document, download, save as `image.<ext>`. Returns path or None |
| `_download_file(file_id, save_path)` | Downloads any Telegram file by file_id via getFile + streaming GET |
| `new_token()` | UUID hex (10 chars) — unique per session |

**Callback data formats:**
- Approval: `APPROVE_{token}` / `REJECT_{token}`
- Schedule: `SCH_{token}_{day_offset}_{hour}` or `PUB_NOW_{token}`
- Choice: `CHOICE_{token}_{code}`
- Duration: `DUR_{token}_{minutes}` or `DUR_{token}_custom`

**File receiving (Telegram → server):**
- Audio: accepts `audio` or `document` messages with `.mp3/.wav/.m4a/.ogg/.flac` extension
- Image: accepts `photo` messages (highest resolution) or `document` with `.png/.jpg/.jpeg`
- Telegram bot file size limit: 50MB — user should send MP3 (not WAV) for music

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

---

### `studio/steps/02_extend.py`

Extends 1 or 2 user-provided clips to target duration (default 20 min, configurable).

**Algorithm:**
1. Auto-discovers `.mp3`/`.wav` files in the draft folder (sorted by name, skips `music.mp3`).
2. Strips silence from each clip (both ends, -50dB threshold).
3. Builds an interleaved sequence (1 clip: `1→1→1…`, 2 clips: `1→2→1→2…`) until ≥ target + 60s.
4. Crossfade-merges segments iteratively (pair-wise) — 6s `acrossfade` with `qsin` curve.
5. Final pass: `dynaudnorm` volume levelling + 3s fade-in + 8s fade-out + trim to exact target.
6. Output: `draft_dir/music.mp3`

---

### `studio/steps/03_assemble.py`

Assembles the final `video.mp4`. Two modes:

**Video clip mode (preferred)** — triggered when `clip.mp4` exists:
- `-stream_loop -1` on the clip (Veo guarantees first == last frame, no dissolve needed)
- Scale to 1920×1080 + 2s fade-in + 3s fade-out

**Static image mode (fallback)** — when no `clip.mp4`:
- Auto-discovers `background.png/jpg` (skips `thumbnail.png/jpg`)
- `-loop 1` on the image + same scale/fade filters

**Logo stamping (`_stamp_logo`):**
- Runs automatically before every static image assembly
- Loads `assets/logo.png` — DhunDetox circular brand logo
- Resizes to 160×160px, applies circular crop (fully opaque, no transparency)
- Pastes at bottom-right corner with 20px padding
- Saves as `image_watermarked.png` and uses that for assembly
- Silently skips if `assets/logo.png` doesn't exist

**Both modes produce:** 1920×1080, H.264, AAC 192k, `+faststart`, duration matches audio exactly.

---

### `studio/steps/04_upload.py`

Thin wrapper: finds `video.mp4` + best available thumbnail → calls `steps/07_upload.py`.  
Thumbnail priority: `thumbnail.png` → `thumbnail.jpg` → `background.png` → `background.jpg`.  
Passes `publish_at` through for scheduled publishing.

---

### `studio/orchestrator.py`

Unified entrypoint with mode selection and auto-cleanup.

**`_auto_cleanup()` — runs at every startup:**
- Draft folders **≥3 days old**: deletes `video.mp4` + `music.mp3` (frees ~500MB per post, video already on YouTube)
- Draft folders **≥30 days old**: deletes entire folder
- Parses folder name as `YYYY-MM-DD` date to determine age

**`--draft`**
1. Guards against overwriting: skips if `brain.json` exists unless `--force` passed.
2. Retry loop: up to 3 attempts on rejection.
3. After approval: asks **AUTO or MANUAL** via Telegram inline buttons.

**AUTO mode:**
- Asks target duration → runs Lyria music generation → extends → Gemini image → assembles → upload approval → uploads.

**MANUAL mode:**
- Asks **📱 Telegram** or **💻 Laptop** via inline buttons:
  - **Telegram:** bot waits for `.mp3` file → waits for image → asks duration → extend → assemble → upload approval → uploads. Fully hands-off after sending files.
  - **Laptop:** sends drop-file instructions and exits. User runs `--publish` manually.

**`--publish`** (laptop / AUTO resume)
- Sends Telegram progress updates at each step.
- Skip guards: skips extend if `music.mp3` exists; skips assemble if `video.mp4` is non-empty.
- After assembly: sends Telegram approval (6h timeout) → schedule prompt (3h timeout) → uploads.
- `--date YYYY-MM-DD` to publish a specific draft.

**`--cleanup [--days N]`** (default 30 days)
- Manually delete draft folders older than N days.

---

### `startup.py`

Entry point for cloud deployments (Hetzner / Railway).

1. Reads `YOUTUBE_TOKEN_JSON` env var → base64-decodes → writes `youtube_token.json`
2. Reads `YOUTUBE_CLIENT_SECRET_JSON` env var → base64-decodes → writes `client_secret.json`
3. Runs `studio/orchestrator.py --draft`

Used by the daily cron job on the server.

---

### `setup.sh`

One-command Hetzner server setup. Run as root: `bash setup.sh`

Steps:
1. Install system packages: Python 3.12, FFmpeg, Git, pip
2. Clone repo from GitHub
3. Create Python virtualenv + install `requirements.txt`
4. Interactive prompt for all `.env` values (API keys, playlist IDs)
5. Interactive prompt for base64-encoded `youtube_token.json` + `client_secret.json`
6. Install cron job: `30 2 * * *` (2:30 AM UTC = 8 AM IST)

### `deploy.sh`

Re-deploy script for code updates: `git pull` + `pip install -r requirements.txt`.

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

Before running `--publish` (or sending via Telegram), provide:

| File | Required | Notes |
|---|---|---|
| `clip_1.mp3` | Yes | Primary music clip (Suno or manual recording) |
| `clip_2.mp3` | No | Second variation — interleaved with clip_1 |
| `clip.mp4` | No | 8-second Veo loop — preferred over background image |
| `background.png` | If no clip.mp4 | 1920×1080 Madhubani background (Gemini Pro) |
| `thumbnail.png` | No | High-contrast thumbnail (Gemini Pro, 16:9) |

When sending via **Telegram**: send `.mp3` file first, then image. Bot auto-names them `clip_1.mp3` and `image.png`.

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

**Cloud deployments (Hetzner/Railway):** set these additional env vars (base64-encoded files):
```
YOUTUBE_TOKEN_JSON=<base64 of youtube_token.json>
YOUTUBE_CLIENT_SECRET_JSON=<base64 of client_secret.json>
```

---

## Key Design Decisions

**Plain text descriptions** — YouTube renders `**bold**` and `---` as literal characters. All Markdown was removed from the brain prompt template and a safety strip (`re.sub`) was added in the upload step.

**Tags: curated first, keywords fill** — The `tags[]` array (15 curated terms) takes priority. The `keywords` string fills remaining budget up to 470 chars. This ensures the best terms always appear while maximising discoverability. No per-tag character limit (YouTube only enforces total budget).

**Network retry on upload** — Large video uploads (~400-500MB) occasionally hit `ConnectionResetError` mid-upload. Five attempts with exponential backoff (5→80s) recover without restarting the upload from scratch (resumable upload URI is preserved).

**Brand logo stamp** — Gemini-generated images include a Gemini watermark. `_stamp_logo()` in `03_assemble.py` overlays the DhunDetox circular logo (fully opaque, 160px, bottom-right) before every video assembly, covering the Gemini mark and adding brand identity.

**Auto-cleanup on startup** — Video files (~500MB each) are only needed until upload. `_auto_cleanup()` deletes `video.mp4` + `music.mp3` after 3 days, freeing ~1GB/week automatically. Brain.json and images are kept indefinitely.

**Telegram file receiver** — On a headless server (Hetzner), users can send music and image files directly via Telegram. The bot downloads them, saves to the draft folder, and runs the full pipeline without any laptop interaction.

**Cross-dissolve baked into loop unit** — Simply looping an 8-second clip creates a visible cut at the repeat point. The dissolve is pre-baked into the loop unit (last 0.5s blends into first 0.5s), so `stream_loop -1` produces a seamless 20-minute video.

**Iterative pair-wise crossfade merge** — A single FFmpeg `filter_complex` with 50 audio inputs would exceed graph size limits. Sequential pair-wise merging keeps each FFmpeg call small and reliable.

**Draft overwrite guard** — Re-running `--draft` on a day that already has `brain.json` silently skips unless `--force` is passed, preventing accidental idea replacement.

**Corrupt video guard** — FFmpeg can crash mid-write, leaving a 0-byte `video.mp4`. The orchestrator checks `os.path.getsize(video_path) > 0` and re-assembles if needed.

**Windows-only PATH injection** — `config.py` only injects Shotcut's FFmpeg into PATH on Windows (`os.name == "nt"`). Linux servers (Hetzner) use system FFmpeg installed via `apt`.

---

## Usage Commands

```bash
# Generate today's idea (sends to Telegram for approval)
python studio/orchestrator.py --draft

# Generate idea for a specific date
python studio/orchestrator.py --draft --date 2026-05-27

# Force-regenerate even if brain.json exists
python studio/orchestrator.py --draft --force

# Publish today's draft (after dropping files on laptop)
python studio/orchestrator.py --publish

# Publish a specific date's draft
python studio/orchestrator.py --publish --date 2026-05-25

# Run without Telegram (auto-approve, default durations)
python studio/orchestrator.py --draft --no-telegram

# Delete draft folders older than 30 days
python studio/orchestrator.py --cleanup

# Delete draft folders older than 14 days
python studio/orchestrator.py --cleanup --days 14
```

---

## Deployment (Hetzner VPS)

```bash
# First-time setup (run as root on the server)
bash setup.sh

# Re-deploy after code changes
bash /opt/music-agent/deploy.sh

# Check cron logs
tail -f /var/log/music-agent.log

# Manual test run
cd /opt/music-agent && venv/bin/python studio/orchestrator.py --draft
```

**Cron schedule:** `30 2 * * *` (2:30 AM UTC = 8:00 AM IST)  
**Server spec:** Hetzner CX22 — 2 vCPU, 4GB RAM, ~€3.92/month
