import sys, os
sys.path.insert(0, os.getcwd())
import importlib.util
spec = importlib.util.spec_from_file_location('upload', 'steps/07_upload.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
from googleapiclient.discovery import build
creds = mod._get_credentials()
youtube = build('youtube', 'v3', credentials=creds)

def tag_chars(tags):
    return sum(len(t) + (2 if ' ' in t else 0) for t in tags)

bhupali_tags = [
    'raag bhupali',
    'raga bhupali',
    'bhupali morning raga',
    'sitar sarod tabla',
    'sitar meditation music',
    'sarod music',
    'tabla music',
    'morning prana flow',
    'prana flow music',
    'cortisol reset music',
    'meditation music',
    'healing music',
    'morning meditation',
    'yoga music',
    'pranayama music',
    'indian classical music',
    'raga therapy',
    'sound healing',
    'nervous system calm',
    'dhundetox',
    'morning raga music',
    'sitar music',
    'stress relief music',
    'anxiety relief',
    'energy music',
    'morning energy',
    'bhupali',
]

print(f'Bhupali: {tag_chars(bhupali_tags)}/500, {len(bhupali_tags)} tags')

desc = """Raag Bhupali 432Hz for morning prana flow and cortisol reset. Sitar, Sarod & Tabla — Indian classical meditation music for a calm, energised start.

Before the world demands your attention — give yourself this. Let Raag Bhupali open your breath, clear your morning mind, and restore your prana.

"Rise with your breath. Not with your stress."

0:00 Introduction — Setting the Intention
5:00 Alap — Free Exploration of Raag Bhupali
15:00 Vilambit — Slow Morning Meditation
35:00 Madhya Laya — Deepening the Prana Flow
52:00 Samapti — Resolution & Morning Clarity
58:00 Outro — Carry the Prana Forward

Raag Bhupali is a pentatonic morning raga known for its bright, uplifting clarity. Its five pure notes gently activate the nervous system at dawn — building prana (life force) and replacing cortisol tension with open, grounded energy. The 432Hz tuning amplifies this natural resonance, aligning the body with the rhythm of sunrise.

☀️ PERFECT FOR:
- Morning prana flow and pranayama
- Cortisol reset before the day begins
- Yoga and mindful movement
- Pre-work clarity and focus
- Energising without stimulants
- Starting the week with intention

🎵 WHY RAAG BHUPALI HEALS:
Bhupali's pentatonic structure creates an uplifting yet grounded soundscape that gently builds morning energy without anxiety. The sitar's brightness, sarod's warmth, and tabla's grounded pulse work together to restore natural prana flow and prepare the mind for the day ahead.

────────────────────────────

🇮🇳 हिंदी में:
सुबह जब ऊर्जा की ज़रूरत हो — राग भूपाली 432Hz आपके प्राण को जागृत करता है। सितार, सरोद और तबला की मधुर धुन से कॉर्टिसोल कम होता है और मन स्वच्छ और तैयार होता है।
"अपनी सांस के साथ उठें। तनाव के साथ नहीं।"

────────────────────────────

💛 If this music brought you stillness, please LIKE, SUBSCRIBE, and SHARE with someone who needs peace.
🔔 Subscribe to DhunDetox for daily Indian classical healing music, raga therapy, and mindful sound journeys.
💬 Comment below: What's your morning intention today?
🌿 Save this video for when you need it most.

────────────────────────────

⚠️ Disclaimer: This music is intended for relaxation and wellness. Not a substitute for professional medical treatment.

#meditationmusic #indianclassicalmusic #healingmusic #morningmeditation #ragamusic #sitarmusic #soundhealing #ragatherapy #pranayama #yogamusic #dhundetox #राग_भूपाली #तनावमुक्ति #मनशांति #सुबहकाध्यान"""

youtube.videos().update(part='snippet', body={'id': 'MrD7VbR0TJw', 'snippet': {
    'title': 'When Your Morning Needs a Reset ☀️ Raag Bhupali 432Hz | Sitar, Sarod & Tabla for Prana Flow',
    'description': desc,
    'tags': bhupali_tags,
    'categoryId': '10',
}}).execute()
print('Bhupali updated successfully.')
