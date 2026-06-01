import subprocess, sys, os, json
from PIL import Image, ImageDraw

draft = 'studio/drafts/2026-06-01'
wavs = [
    f'{draft}/Velvet Comet.wav',
    f'{draft}/Velvet Comet (1).wav',
    f'{draft}/Komal Lantern.wav',
    f'{draft}/Komal Lantern (1).wav',
]

# Step 1: crossfade all 4 WAVs into one combined track
print('Step 1: Crossfading 4 WAV clips...')
sys.stdout.flush()
r = subprocess.run([
    'ffmpeg', '-y',
    '-i', wavs[0], '-i', wavs[1], '-i', wavs[2], '-i', wavs[3],
    '-filter_complex',
    '[0:a][1:a]acrossfade=d=5[a12];[a12][2:a]acrossfade=d=5[a123];[a123][3:a]acrossfade=d=5[aout]',
    '-map', '[aout]',
    f'{draft}/combined_audio.wav'
], capture_output=True, text=True)
if r.returncode != 0:
    print('ERROR:', r.stderr[-500:])
    sys.exit(1)

dur = subprocess.run(
    ['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0', f'{draft}/combined_audio.wav'],
    capture_output=True, text=True
)
combined_dur = float(dur.stdout.strip())
print(f'Combined track: {combined_dur:.0f}s ({combined_dur/60:.1f} min)')

# Step 2: loop combined track to exactly 3600s, encode as AAC
print('Step 2: Looping to 60 min...')
sys.stdout.flush()
r = subprocess.run([
    'ffmpeg', '-y',
    '-stream_loop', '-1', '-t', '3600', '-i', f'{draft}/combined_audio.wav',
    '-c:a', 'aac', '-b:a', '256k', '-t', '3600',
    f'{draft}/audio_60min.m4a'
], capture_output=True, text=True)
if r.returncode != 0:
    print('ERROR:', r.stderr[-500:])
    sys.exit(1)
size_mb = os.path.getsize(f'{draft}/audio_60min.m4a') / 1e6
print(f'Audio done: {size_mb:.1f} MB')

# Step 3: build final video — static image + pre-encoded audio (no filters on audio)
print('Step 3: Building 60-min video...')
sys.stdout.flush()
scale = 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black'
r = subprocess.run([
    'ffmpeg', '-y',
    '-loop', '1', '-i', f'{draft}/image_watermarked.png',
    '-i', f'{draft}/audio_60min.m4a',
    '-vf', f'{scale},fade=t=in:st=0:d=2,fade=t=out:st=3597:d=3',
    '-map', '0:v', '-map', '1:a',
    '-t', '3600',
    '-c:v', 'libx264', '-tune', 'stillimage', '-preset', 'fast', '-crf', '20',
    '-c:a', 'copy',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    f'{draft}/video.mp4'
], capture_output=True, text=True)
if r.returncode != 0:
    print('ERROR:', r.stderr[-1000:])
    sys.exit(1)

size_gb = os.path.getsize(f'{draft}/video.mp4') / 1e9
print(f'Video done: {size_gb:.2f} GB')
print('Ready to upload.')
