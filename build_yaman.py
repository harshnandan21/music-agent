import subprocess, sys, os, math
from PIL import Image, ImageDraw

draft = 'studio/drafts/2026-06-02'
LOGO_SIZE    = 180
LOGO_CX_PCT  = 0.955
LOGO_CY_PCT  = 0.930
XFADE_DUR    = 0.5
AUDIO_CF_DUR = 5  # crossfade between audio clips

# ── Stamp logo on image ───────────────────────────────────────────────────
img_src = f'{draft}/ChatGPT Image Jun 2, 2026, 12_58_51 PM (1).png'
logo = Image.open('assets/logo.png').convert('RGBA')
logo = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
mask = Image.new('L', (LOGO_SIZE, LOGO_SIZE), 0)
ImageDraw.Draw(mask).ellipse((0, 0, LOGO_SIZE-1, LOGO_SIZE-1), fill=255)
logo.putalpha(mask)
bg = Image.open(img_src).convert('RGBA')
cx = int(bg.width * LOGO_CX_PCT)
cy = int(bg.height * LOGO_CY_PCT)
bg.paste(logo, (cx - LOGO_SIZE//2, cy - LOGO_SIZE//2), logo)
img_out = f'{draft}/image_watermarked.png'
bg.convert('RGB').save(img_out, 'PNG')
print(f'Logo stamped at ({cx},{cy}), image size {bg.width}x{bg.height}')

# ── Probe animated clip ───────────────────────────────────────────────────
clip_path = f'{draft}/For_Gemini_Video_Veo_you_ne.mp4'
r = subprocess.run(['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0',clip_path],
    capture_output=True, text=True)
clip_dur = float(r.stdout.strip())
print(f'Clip duration: {clip_dur}s')

# ── Pre-encode 60-min audio ───────────────────────────────────────────────
wavs = [
    f'{draft}/Evening Yaman Drift.wav',
    f'{draft}/Evening Yaman Drift (1).wav',
]
print('Preparing audio: crossfade + loop to 3600s...')
sys.stdout.flush()

# Crossfade 2 WAVs
combined = f'{draft}/combined_audio.wav'
r = subprocess.run([
    'ffmpeg', '-y',
    '-i', wavs[0], '-i', wavs[1],
    '-filter_complex', f'[0:a][1:a]acrossfade=d={AUDIO_CF_DUR}[aout]',
    '-map', '[aout]', combined
], capture_output=True, text=True)
if r.returncode != 0:
    print('Audio crossfade ERROR:', r.stderr[-500:]); sys.exit(1)

# Loop to 3600s as AAC
audio_final = f'{draft}/audio_60min.m4a'
r = subprocess.run([
    'ffmpeg', '-y',
    '-stream_loop', '-1', '-t', '3600', '-i', combined,
    '-c:a', 'aac', '-b:a', '256k', '-t', '3600', audio_final
], capture_output=True, text=True)
if r.returncode != 0:
    print('Audio loop ERROR:', r.stderr[-500:]); sys.exit(1)
print(f'Audio ready: {os.path.getsize(audio_final)/1e6:.1f} MB')

# ── Build video: animated clip looped with xfade dissolve ────────────────
duration   = 3600.0
eff_dur    = clip_dur - XFADE_DUR
n_clips    = max(2, math.ceil((duration - clip_dur) / eff_dur) + 1)
scale      = ('scale=1920:1080:force_original_aspect_ratio=decrease,'
              'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black')

print(f'Building video: {n_clips} clips with {XFADE_DUR}s dissolve...')
sys.stdout.flush()

inputs = []
for _ in range(n_clips):
    inputs += ['-i', clip_path]
inputs += ['-i', audio_final]
inputs += ['-i', img_out]  # logo already stamped on image — not needed separately

# Scale + xfade chain
parts = [f'[{i}:v]{scale}[sv{i}]' for i in range(n_clips)]
prev = '[sv0]'
for i in range(1, n_clips):
    offset = i * eff_dur
    label = f'[xf{i}]'
    parts.append(f'{prev}[sv{i}]xfade=transition=dissolve:duration={XFADE_DUR}:offset={offset:.3f}{label}')
    prev = label
fade_out = duration - 3
parts.append(f'{prev}fade=t=in:st=0:d=2,fade=t=out:st={fade_out:.1f}:d=3[v]')

music_idx = n_clips
fc = ';'.join(parts)

cmd = ['ffmpeg', '-y'] + inputs + [
    '-filter_complex', fc,
    '-map', '[v]', '-map', f'{music_idx}:a',
    '-t', str(duration),
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
    '-c:a', 'copy',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    f'{draft}/video.mp4'
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print('Video ERROR:', result.stderr[-1000:]); sys.exit(1)

size = os.path.getsize(f'{draft}/video.mp4') / 1e9
print(f'Done! {size:.2f} GB — ready to upload.')
