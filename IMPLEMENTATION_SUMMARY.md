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
            │  raga, title, 8 SEO titles, description, keywords, chapters, image/music/video prompts
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
│   ├── logo.png                 # DhunDetox circular brand logo (source)
│   └── logo_Npx.png             # Cached circular logo at specific size (generated)
├── steps/
│   ├── 01_brain.py              # Gemini idea generator (title, description, prompts, chapters)
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
├── build_chandrakauns.py        # One-off build script for 2026-06-01 post
├── build_yaman.py               # One-off build script for 2026-06-02 post
├── update_tags.py               # Utility: backfill tags on existing YouTube videos
├── update_bhupali.py            # Utility: backfill SEO improvements for Bhupali post
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

**What Gemini writes:** title (if not locked), 8 SEO-optimised title options, description, keywords, tags, chapters, music_prompt, image_prompt, video_prompt, hook_angle, hook_phrase, thumbnail_hook, thumbnail_tagline.

**Hard constraints:** any field set in `WEEKLY_SCHEDULE` is passed in a `LOCKED VALUES` section and then force-merged into the output via `data.update(locked)` — Gemini cannot override them.

**8 SEO Title Patterns (competitor research-based):**
Each title ≤70 chars, includes raga + Hz + instruments + use-case benefit. 8 patterns generated per post:
- Pattern A: Benefit-first — `"Melt Evening Stress | Raga X | Sitar & Bansuri 174Hz"`
- Pattern B: Hz-first — `"174Hz Cortisol Drop | Raga X | Sitar & Bansuri Evening"`
- Pattern C: Intent-first — `"Unwind After Work | Yaman Kalyan Sitar & Bansuri | 174Hz"`
- Pattern D: Compound phrase — `"Evening Raga for Stress Relief | Raga X | Sitar 174Hz"`
- Pattern E: Emotional hook — `"Release the Day 🌆 Raag X 174Hz | Sitar & Bansuri"`
- Pattern F: Proven keyword — `"Lower Cortisol with Raga X | 174Hz Sitar & Bansuri"`
- Pattern G: Frequency-first — `"174Hz Evening Calm | Raag X | Indian Sitar & Flute"`
- Pattern H: Compressed hook — `"Stress Melt 🌆 Raag X 174Hz | Sitar & Bansuri Evening"`

**Description template (300–400 words, 9 sections):**
1. First 125 chars: keyword-first (no emoji at start) — shown before "Show More"
2. 2–3 sentence hook (pain point, punchy)
3. Hook phrase (quoted)
4. Chapters (0:00 → 58:00) — YouTube indexes these as keywords
5. Raga cultural context (2–3 sentences)
6. PERFECT FOR: 6 bullet points
7. WHY RAAG X HEALS: 2 sentences (parasympathetic + Hz science)
8. Hindi section (3–4 lines + translated hook phrase)
9. CTA + Disclaimer + 15 hashtags

**`chapters` field in brain.json:**
```json
"chapters": [
  {"time": "0:00", "title": "Introduction — Setting the Intention"},
  {"time": "5:00", "title": "Alap — Free Exploration of Raag X"},
  {"time": "15:00", "title": "Vilambit — Slow & Deep Meditation"},
  {"time": "35:00", "title": "Madhya Laya — Deepening the Stillness"},
  {"time": "52:00", "title": "Samapti — Resolution & Inner Peace"},
  {"time": "58:00", "title": "Outro — Carry the Calm Forward"}
]
```

**Keyword string:** 470-480 chars, comma-separated, no spaces after commas. Pattern: raga variations → instrument+raga combos → instrument alone → meditation/healing terms → emotion terms → channel name → Hindi keywords at end.

**Tags:** 20–24 quality tags, targeting 440–460 chars total budget (YouTube allows 500 but rejects above ~465 in practice). English-only (ASCII filter). First tag = primary keyword (raag name).

**Anti-repeat tracking:** last 20 published ideas loaded from `used_ideas.json`; titles + dates injected into prompt so Gemini avoids repeated angles.

---

### `steps/07_upload.py`

Uploads to YouTube via Data API v3 with OAuth 2.0.

**Tag building logic:**
1. Start with curated `tags[]` array (priority, best terms)
2. Fill remaining budget from `keywords` string
3. ASCII filter (no Hindi tags — YouTube rejects them)
4. Total budget: 470 chars (YouTube hard-rejects above ~465 in practice)
5. No per-tag length limit

**Key behaviours:**
- Network retry: infinite retries with 30s wait on any network error (keeps resumable upload URI alive through connection drops).
- Strips Markdown from description: removes `*`/`**`, replaces `---` with `────────────────────────────`.
- Scheduling: if `publish_at` (RFC3339 UTC string) is passed → `privacyStatus: private` + `publishAt`; otherwise → `public`. Must set during initial upload (cannot reschedule a video that's already public).
- Thumbnail: PIL JPEG compression loop (quality 85 → 70 → 55 → 40) to stay under YouTube's 2MB limit.
- Playlist: looks up playlist ID by key from `brain["playlist"]` → calls `playlistItems().insert()`.
- Scopes include `youtube.force-ssl` for comment posting support.

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

**File receiving (Telegram → server):**
- Audio: accepts `audio` or `document` messages with `.mp3/.wav/.m4a/.ogg/.flac` extension
- Image: accepts `photo` messages (highest resolution) or `document` with `.png/.jpg/.jpeg`
- Telegram bot file size limit: 50MB — user should send MP3 (not WAV) for music

---

### `studio/steps/01_draft.py`

Phase 1 of the studio workflow.

1. Runs `steps/01_brain.py` via `importlib.util` (handles digit-prefixed module names).
2. Saves `brain.json` to `studio/drafts/YYYY-MM-DD/`.
3. Sends Telegram approval message with idea summary + all 8 title options.
4. Sends a `.txt` document with all prompts bundled (easy copy-paste on phone):
   - **Suno Custom Mode:** style field + structural lyrics markers
   - **Gemini Pro — Background Image:** wraps `brain["image_prompt"]`
   - **Veo — Video Prompt:** 8-second seamless loop animation guide
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
- Two-stage build to avoid Windows command-line length limits:
  - Stage 1: 32 clips × xfade dissolve (0.5s) → `segment_5min.mp4` (~5 min)
  - Stage 2: `stream_loop -1` on segment → 60-min final video
- Pre-encodes audio separately (crossfade clips → loop to duration as AAC) before combining — avoids `aloop` filter which causes YouTube processing to get stuck
- Logo overlay via FFmpeg: centered at 95.5% x / 93% y of frame

**Static image mode (fallback)** — when no `clip.mp4`:
- Accepts single path or list of audio files
- Pre-encodes audio: `acrossfade=d=5` between clips → loop to full duration as AAC file → `-c:a copy` in final video
- `-loop 1` on the watermarked image + scale/fade filters
- Uses `-vf` (simple filter) for video, `-map 1:a` for pre-encoded audio stream

**Logo stamping (`_stamp_logo`):**
- Runs automatically before every static image assembly
- `LOGO_SIZE = 180px` — large enough to fully cover Gemini/AI watermarks
- Position: centered at `cx = width × 95.5%`, `cy = height × 93%` — mathematically ensures logo stays fully within 1920×1080 video frame after FFmpeg scaling (bottom: 1051/1080px, right: 1895/1920px)
- `_make_circular_logo(size)` — creates circular PNG from `assets/logo.png`, cached as `assets/logo_Npx.png`
- Silently skips if `assets/logo.png` doesn't exist

**Both modes produce:** 1920×1080, H.264 CRF 20, AAC 256kbps, `+faststart`.

---

### `studio/steps/04_upload.py`

Thin wrapper: finds `video.mp4` + best available thumbnail → calls `steps/07_upload.py`.  
Thumbnail priority: `thumbnail.png` → `thumbnail.jpg` → `background.png` → `background.jpg` → any PNG/JPG in draft folder.  
Passes `publish_at` through for scheduled publishing.

---

### `studio/orchestrator.py`

Unified entrypoint with mode selection and auto-cleanup.

**`_auto_cleanup()` — runs at every startup:**
- Draft folders **≥3 days old**: deletes `video.mp4` + `music.mp3` (frees ~500MB per post)
- Draft folders **≥30 days old**: deletes entire folder

**`--draft`** → Gemini generates idea → Telegram approval → AUTO or MANUAL mode selection

**MANUAL mode** → **📱 Telegram** or **💻 Laptop** sub-choice

**`--publish`** → extend → assemble → Telegram upload approval → schedule prompt → upload

---

### `startup.py`

Entry point for cloud deployments (Hetzner / Railway).

1. Reads `YOUTUBE_TOKEN_JSON` env var → base64-decodes → writes `youtube_token.json`
2. Reads `YOUTUBE_CLIENT_SECRET_JSON` env var → base64-decodes → writes `client_secret.json`
3. Runs `studio/orchestrator.py --draft`

---

## YouTube SEO Strategy

### Tags
- **Budget:** 440–460 chars (YouTube shows 500 but rejects above ~465 in practice)
- **Count:** 20–24 quality tags
- **Order:** primary keyword first, then raga variations, instruments, broad categories, long-tail combos, brand last
- **No Hz terms** in the keywords string (YouTube may flag medical/frequency claims)

### Description
- **First 125 chars:** keyword-first, no emoji at start — shown before "Show More" button
- **Chapters:** baked in after the hook — YouTube indexes each chapter title as a mini-keyword
- **Length:** 300–400 words (not 1000+ — shorter descriptions get better engagement)
- **Hindi section:** kept — unique SEO advantage, captures Hindi search traffic competitors miss
- **Hashtags:** exactly 15 (YouTube ignores all if >15)

### Title Patterns
8 options generated per post across patterns: benefit-first, Hz-first, intent-first, compound phrase, emotional hook, proven keyword, frequency-first, compressed hook.

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

---

## Drop Files Reference

| File | Required | Notes |
|---|---|---|
| `clip_1.mp3` | Yes (static mode) | Primary music clip (Suno) |
| `clip_2.mp3` | No | Second variation — interleaved with clip_1 |
| `clip.mp4` | No | 8–10s animated loop (Kling/Veo) — preferred for richer visuals |
| `background.png` | If no clip.mp4 | 16:9 Madhubani background (Gemini Pro) |
| `thumbnail.png` | No | High-contrast thumbnail with baked-in text |

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

**Pre-encoded audio (no aloop filter)** — The FFmpeg `aloop` filter creates non-standard audio streams that cause YouTube to get stuck in "processing" state for hours. All builds now pre-encode audio in two steps: (1) crossfade clips → combined WAV, (2) loop to target duration as AAC file, then use `-c:a copy` in the final video. This produces standard streams YouTube processes within minutes.

**Logo covers AI watermark** — AI image generators (Gemini, ChatGPT, Kling) embed watermarks at ~96-97% of image dimensions. Logo size 180px centered at `width × 95.5% / height × 93%` covers the watermark while keeping the full circle visible in the 1080p video frame (math: bottom at 1051/1080px, right at 1895/1920px after FFmpeg scaling).

**Two-stage animated video build** — 379 FFmpeg inputs (for 60-min from a 10s clip) exceeds Windows command-line length limit (32,767 chars). Solution: build a ~5-min segment from 32 clips with xfade dissolve, then use `stream_loop -1` on the segment for the full 60-min video.

**8 SEO title patterns** — Research from top channels (Meditative Mind, Greenred Productions, Yellow Brick Cinema) showed benefit-first and Hz-first titles outperform emotional/poetic hooks for discoverability. Gemini now generates 8 options per post across all proven patterns.

**Audio crossfade between clips (5s)** — `acrossfade=d=5` between Suno-generated clips creates a smooth 5-second overlap instead of an abrupt join. Used in both the pre-encode step (multi-clip audio) and the extend step.

**Tags: 440–460 chars safe zone** — YouTube's API rejects tags above ~465 chars despite showing "500/500" limit in Studio. Discovered empirically. Brain prompt targets 440–460 to stay safe.

**Description chapters** — YouTube indexes each chapter title as a searchable keyword. Adding 6 chapters per video (0:00 → 58:00) effectively adds 6 more keyword-rich entries to YouTube's index for free.

**Quality first, CRF 20** — Audio and video quality is the primary product. CRF 20 (high quality) is maintained for all output. File size (5GB for animated 60-min) is accepted as the trade-off.

**Network retry on upload** — Infinite retry with 30s wait on any network error preserves the resumable upload URI through connection drops. Previous 5-attempt limit was too aggressive for large files on unstable connections.

**Plain text descriptions** — YouTube renders `**bold**` and `---` as literal characters. All Markdown removed from brain prompt; safety strip (`re.sub`) in upload step handles any leftovers.

**Auto-cleanup on startup** — Video files (~500MB–5GB each) only needed until upload. `_auto_cleanup()` deletes `video.mp4` + `music.mp3` after 3 days, freeing space automatically.

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
