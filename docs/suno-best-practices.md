# DhunDetox × Suno — Music Generation Best Practices

## How Suno Processes Prompts

Suno reads three layers simultaneously:

| Layer | Field | What it controls |
|---|---|---|
| **Style tags** | STYLE | Genre, instrument, mood, production — most powerful |
| **Structure markers** | LYRICS | Arrangement, sections, pacing |
| **Song description** | TITLE | Emotional arc, intent |

**The #1 rule:** Write comma-separated tag stacks, not sentences. Suno is a search engine for sound, not a language model. `meditative, sparse, spiritual calm` works. *"A meditative and spiritually calm piece"* does not.

---

## The Master Formula (DhunDetox Template)

```
Raga [NAME], Indian classical instrumental, [THAAT] thaat, [TIME OF DAY],
[PRIMARY INSTRUMENT] [role], [SECONDARY INSTRUMENT] [role],
[BPM] BPM, [TAAL or "no taal"], alap-jor-jhala structure,
[3-4 mood tags],
cinematic warmth, emotional depth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade
```

### Filled example — Raga Vibhas / Sarangi

```
Raga Vibhas, Indian classical instrumental, Bhairav thaat, midnight,
sarangi lead, bowed sarangi, crying Indian strings, intimate bowed lute, tanpura drone,
35 BPM, no taal, alap-jor-jhala structure,
meditative, introspective, spiritual calm, healing resonance,
cinematic warmth, emotional depth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade
```

---

## Proven Templates by Content Type

### Deep Sleep / Midnight
```
Raga [NAME], Indian classical instrumental, [THAAT] thaat, late night raga,
[instrument] lead, tanpura drone,
35 BPM, no taal, alap-jor-jhala structure,
deeply melancholic, introspective, meditative stillness, void-like calm,
cinematic warmth, emotional depth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade
```

### Morning / Sunrise
```
Raga [NAME], Indian classical instrumental, [THAAT] thaat, sunrise raga,
bansuri flute melody, [secondary instrument] support, [taal] tabla,
vilambit laya transitioning to madhya laya, alap-jor-jhala structure,
serene awakening, hopeful, spiritually uplifting, healing resonance,
cinematic warmth, emotional depth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade
```

### Stress Relief / Anxiety
```
Raga [NAME], Indian classical instrumental, [THAAT] thaat, evening raga,
[instrument] lead, [secondary] support, tabla 40 BPM,
alap-jor-jhala structure, vilambit laya,
emotional release, bittersweet longing, cortisol drop, healing resonance,
cinematic warmth, emotional depth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade
```

### Focus / Deep Work
```
Raga [NAME], Indian classical instrumental, [THAAT] thaat, evening raga,
sitar lead, tanpura drone, tabla 55 BPM,
alap-jor-jhala structure, calm concentration,
intellectual clarity, meditative, sparse arrangement, no percussion drop,
cinematic warmth, emotional depth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade
```

### Meditation / Chakra
```
Raga [NAME], Indian classical instrumental, [THAAT] thaat, midnight raga,
tanpura continuous drone, [instrument] pure alap, no rhythm section,
nada yoga style, peaceful void, chakra balancing, theta wave feel,
10-minute loop-friendly structure, cinematic warmth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
no lyrics, no western percussion, DhunDetox wellness channel, loop-friendly fade
```

---

## Lyrics Field — Structural Markers by Category

The LYRICS field controls arrangement. Always use structural markers, never actual lyrics.

### Midnight / Deep Sleep
```
[Heavy Alap — primary instrument alone, gravity in every note, 10-second silences]
[Deliberate Stillness — thoughts settling like sediment, no hurry]

[Slow Gat — rhythm enters at 3+ minutes, minimal, ancient pulse]
[Sustained Meditation — no buildup, no climax, just the midnight]

[Fade into silence — the music becomes the room, then nothing]
```

### Morning / Sunrise
```
[Gentle Alap — instrument opens softly, ascending phrases like sunrise]
[Awakening — warmth building, not urgency, a slow opening]

[Madhya Laya — mid-pace steady energy, second instrument enters]
[Open Flow — brightness without force, breathing with the music]

[Gentle Close — leave room to start the day, no dramatic ending]
```

### Stress / Anxiety Release
```
[Slow Alap — instrument enters alone, no rhythm, emotional release begins]
[Komal phrases — longing held, then released, like exhaling weeks of tension]

[Gentle Gat — rhythm enters softly, breath-paced, second instrument joins]
[Emotional Release — phrases that sigh and resolve, the weight lifting]

[Fade — cortisol dropping, nervous system finally resting]
```

### Focus / Deep Work
```
[Slow Alap — instrument solo, methodical, each phrase deliberate]
[Deep Concentration — wide silence between phrases, thought completing itself]

[Vilambit Gat — sparse rhythm enters, laser stillness, no distraction]
[Extended Flow — sustained clarity, no climax, no break in concentration]

[Open Awareness — no resolution, just sustained focus]
```

---

## Instrument Tag Reference

Always include these extended tags for rare instruments — Suno needs the hint:

| Instrument | Extra tags to add |
|---|---|
| **Sarangi** | `bowed sarangi, crying Indian strings, intimate bowed lute` |
| **Pakhawaj** | `pakhawaj barrel drum, dhrupad percussion, ancient deep drum` |
| **Mridangam** | `mridangam South Indian drum, Carnatic rhythm, two-headed drum` |
| **Shehnai** | `shehnai reed, ceremonial Indian oboe, nadaswaram style` |
| **Veena** | `veena ancient plucked string, Saraswati veena, sustained resonance` |
| **Esraj** | `esraj bowed string, Bengali classical, haunting resonance` |
| **Santoor** | `santoor hammered dulcimer, Kashmir, shimmering sustain` |
| **Sarod** | `sarod fretless metal string, deep resonance, Dhrupad feel` |

Common instruments (Suno handles these without hints): `sitar, bansuri, tabla, tanpura, harmonium`

---

## Mood Tags That Work in Suno

```
meditative, introspective, melancholic longing, serene, devotional,
raga alap style, vilambit laya, nada yoga, spiritual calm,
healing resonance, bittersweet, deeply contemplative,
peaceful void, emotional catharsis, sacred stillness
```

## Production Tags That Improve Output

```
high fidelity recording, concert hall acoustics, AIR Studios quality,
warm analog feel, cinematic warmth, no compression artifacts,
wide stereo field, natural reverb decay, organic recording
```

---

## Suno Pro Features — How to Use Each

| Feature | When to use | How |
|---|---|---|
| **Custom mode** | Always | Separate Style, Lyrics, Title fields — never use Simple mode |
| **Instrumental toggle** | Always ON | Vocals destroy classical authenticity |
| **Generate variations** | Every session | Generate 6 clips across 3 energy levels (see DhunDetox 6-clip workflow below) |
| **Remaster** | After generating | Run each clip through Remaster for cleaner audio |
| **Inpainting** | Fix weak sections | If tabla drops out unnaturally or a phrase sounds wrong, use inpainting to fix that region |
| **Download stems** | Optional refinement | Download stems and layer/refine in Audacity or GarageBand |

---

## What `alap-jor-jhala structure` Does

This tag instructs Suno to follow the authentic Hindustani classical 3-act form:

| Section | What happens | Suno output |
|---|---|---|
| **Alap** | Unmetered, free exploration of raga | Sparse, slow, no rhythm — opening 30-40% |
| **Jor** | Rhythmic but still free, no tabla | More movement, pulse emerges — middle section |
| **Jhala** | Faster, rhythmic conclusion | Energy builds toward end — closing 15-20% |

Without this tag, Suno generates a loop or pop structure (verse/chorus). With it, the piece has a real classical shape.

---

## Raga × Time of Day Reference

| Raga | Time | Mood |
|---|---|---|
| Bhairav | Sunrise (4-7 AM) | Serene awakening, devotional, spiritual |
| Ahir Bhairav | Early morning | Gentle melancholy, introspective |
| Yaman | Sunset / evening | Beauty, romance, clarity |
| Yaman Kalyan | Early evening | Peaceful, graceful |
| Darbari Kanada | Late night | Deep, heavy, royal melancholy |
| Bageshri | Midnight | Devotional longing, yearning |
| Vibhas | Pre-dawn / midnight | Austere stillness, void, 5-note purity |
| Bhairavi | Any time (farewell raga) | Bittersweet, emotional release |
| Chandrakauns | Midnight | Mysterious, introspective, no Pa |
| Bhupali | Sunset | Joyful, open, pentatonic brightness |
| Kafi | Monsoon / spring | Earthy, melancholic, folk roots |

---

## Common Mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| Writing sentences in Style | Suno ignores prose grammar | Use comma-separated tags only |
| Mixing Carnatic + Hindustani | Suno gets confused — two different systems | Pick one system per prompt |
| Skipping BPM | Suno defaults to pop tempo (~120 BPM) | Always specify BPM (35-55 for meditation) |
| "Lyrics" mode for alap | Vocals appear or arrangement goes wrong | Always use Instrumental toggle ON |
| Vague mood tags | "peaceful and beautiful" → generic output | Be specific: `vilambit laya, melancholic longing` |
| Beat-heavy tags | Pollutes classical feel | Never: EDM drop, bass boost, trap beat |
| Accepting first generation | First clip is rarely the best | Always generate 4-6, compare |
| Not extending | Short clip loops unnaturally | Extend 2-3× then Remaster |

---

## DhunDetox 6-Clip Workflow

Generate 6 clips per post — 3 energy levels × 2 variations. The pipeline interleaves all 6 so the same clip doesn't repeat for ~24 min. A single looped track risks a YouTube "inauthentic content" flag.

**Energy level structure:**
| Clips | Level | Style |
|---|---|---|
| 1–2 | SPARSE | Solo bansuri dominant, no tabla or very faint, very slow, alap-like, long silences |
| 3–4 | MEDIUM | Full trio building, tabla enters gently, 38–45 BPM, meditative flow |
| 5–6 | FULL | Full trio peak, bansuri freely flowing, sarod warm, tabla conversational, 48–50 BPM |

**Each prompt has:**
- **STYLE FIELD** — base style tags + section-specific modifiers (this is what Suno actually processes)
- **LYRICS FIELD** — only simple bracket markers like `[Slow Alap]`, `[Steady Flow]`, `[Morning Peak]` — no descriptive prose, Suno ignores it

## End-to-End Workflow

```
1. Pick raga → note its thaat, time of day, emotional quality
2. Run --draft to get all 6 Suno prompts (3 energy × 2 variations)
3. In Suno: use Custom Mode, Instrumental ON
4. Generate each of the 6 prompts → Remaster each clip
5. Use Inpainting if any section sounds wrong
6. Download as WAV → name 1.wav, 2.wav, 3.wav, 4.wav, 5.wav, 6.wav
   (alphabetical sort = playback order: sparse first, full last)
7. Drop all 6 WAVs into studio/drafts/YYYY-MM-DD/
8. Also drop: clip_1.mp4…clip_4.mp4 (Veo), background.png (Gemini), thumbnail.png
9. Run: python studio/orchestrator.py --publish --date YYYY-MM-DD
10. Pipeline extends all 6 clips to natural 60–70 min, assembles, uploads
```

---

## DhunDetox Brand Signature

Save this as your base — modify only the raga, time, instruments, and mood tags:

```
Raga [INSERT], Indian classical instrumental, [THAAT] thaat, [TIME],
[PRIMARY INSTRUMENT] lead, tanpura drone,
[BPM] BPM, [taal or "no taal"], alap-jor-jhala structure,
meditative healing, no lyrics, no western percussion,
cinematic warmth, emotional depth, spiritual stillness,
high fidelity recording, concert hall acoustics, AIR Studios quality, warm analog feel,
DhunDetox wellness channel, loop-friendly fade
```
