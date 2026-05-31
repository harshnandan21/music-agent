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

bhairavi_tags = [
    'raag bhairavi',
    'raga bhairavi',
    'bhairavi morning raga',
    'bansuri meditation',
    'tanpura drone',
    'bansuri flute music',
    'indian flute music',
    'meditation music',
    'healing music',
    'stress relief music',
    'morning cortisol reset',
    'new week calm',
    'anxiety relief music',
    'cortisol reset music',
    'indian classical music',
    'raga therapy',
    'sound healing',
    'nervous system calm',
    'dhundetox',
    'morning raga music',
    'bansuri healing',
    'calm music',
    'bhairavi raga',
    'new week music',
    'focus music',
    'mind calm music',
]

darbari_tags = [
    'raag darbari kanada',
    'darbari kanada',
    'darbari kanada meditation',
    'sitar meditation music',
    'sitar music',
    'bansuri flute',
    'tabla music',
    'sleep music',
    'meditation music',
    'overthinking relief',
    'midnight calm music',
    'overactive mind relief',
    'anxiety relief music',
    'insomnia relief music',
    'late night meditation',
    'indian classical music',
    'raga therapy',
    'sound healing',
    'nervous system calm',
    'dhundetox',
    'deep sleep music',
    'stress relief music',
    'darbari raga',
    'night music',
    'sitar bansuri',
]

print(f'Bhairavi: {tag_chars(bhairavi_tags)}/500, {len(bhairavi_tags)} tags')
print(f'Darbari:  {tag_chars(darbari_tags)}/500, {len(darbari_tags)} tags')

bhairavi_desc = """Raag Bhairavi 432Hz for morning cortisol reset. Bansuri & Tanpura deep meditation music for stress relief and new week calm.

Is the new week already weighing on you before it begins? Before the demands start, give yourself this stillness.

"Lower your cortisol. Slow your breath. Let this raga do the rest."

0:00 Introduction — Setting the Intention
5:00 Alap — Free Exploration of Raag Bhairavi
15:00 Vilambit — Slow & Deep Meditation
35:00 Madhya Laya — Deepening the Stillness
52:00 Samapti — Resolution & Inner Peace
58:00 Outro — Carry the Calm Forward

Raag Bhairavi, traditionally performed at dawn, is considered the most emotionally complete raga in Indian classical music. Its all-komal (flat) notes gently guide the nervous system into a parasympathetic state — from fight-or-flight to rest-and-restore. The 432Hz tuning deepens this effect, aligning the body with natural rhythms before the week begins.

\U0001f305 PERFECT FOR:
- Morning cortisol reset before work
- Starting the new week with calm
- Releasing Sunday night dread
- Pre-meeting anxiety relief
- Surrender meditation practice
- Mindful, gentle awakening

\U0001f3b5 WHY RAAG BHAIRAVI HEALS:
Bhairavi's melodic structure, delivered through the soft bansuri over a steady tanpura drone, directly activates the parasympathetic nervous system — slowing breath and heart rate within minutes. Paired with 432Hz, it dissolves the tension of new beginnings and replaces it with grounded acceptance.

────────────────────────────

\U0001f1ee\U0001f1f3 हिंदी में:
जब नया हफ़्ता भारी लगे — राग भैरवी 432Hz आपकी सुबह को शांत करता है। बांसुरी और तानपुरा की मधुर धुन से कॉर्टिसोल कम होता है और मन नए सप्ताह के लिए तैयार होता है।
"अपने कॉर्टिसोल को कम करें। अपनी सांस धीमी करें। बाकी काम इस राग को करने दें।"

────────────────────────────

\U0001f49b If this music brought you stillness, please LIKE, SUBSCRIBE, and SHARE with someone who needs peace.
\U0001f514 Subscribe to DhunDetox for daily Indian classical healing music, raga therapy, and mindful sound journeys.
\U0001f4ac Comment below: What does surrender mean to you as you begin a new week?
\U0001f33f Save this video for when you need it most.

────────────────────────────

⚠️ Disclaimer: This music is intended for relaxation and wellness. Not a substitute for professional medical treatment.

#meditationmusic #indianclassicalmusic #healingmusic #stressrelief #ragamusic #bansuriflute #soundhealing #ragatherapy #morningmeditation #cortisol #dhundetox #राग_भैरवी #तनावमुक्ति #मनशांति #सुबहकाध्यान"""

darbari_desc = """Raag Darbari Kanada 396Hz for overactive mind and midnight calm. Sitar, Bansuri & Tabla for late-night overthinking relief and deep sleep.

Is your mind racing tonight? Thoughts looping, sleep out of reach — put the world down. For now, nothing is your problem.

"Lower your cortisol. Slow your breath. Let this raga do the rest."

0:00 Introduction — Setting the Intention
5:00 Alap — Free Exploration of Raag Darbari Kanada
15:00 Vilambit — Slow & Deep Meditation
35:00 Madhya Laya — Deepening the Stillness
52:00 Samapti — Resolution & Inner Peace
58:00 Outro — Carry the Calm Forward

Raag Darbari Kanada is one of the most revered night ragas in Indian classical music, known for its profound gravity and depth. Its deep komal rishab and komal gandhar settle restless thoughts like sediment at the bottom of still water. Combined with 396Hz — the frequency of emotional liberation — this music dissolves the mental weight of the day and guides you to profound stillness.

\U0001f319 PERFECT FOR:
- Silencing overthinking at night
- Achieving deep, restorative sleep
- Calming an anxious nervous system
- Releasing daily stress and tension
- Pre-sleep meditation practice
- Late-night emotional reset

\U0001f3b5 WHY RAAG DARBARI KANADA HEALS:
Darbari Kanada's characteristic deep notes activate the parasympathetic nervous system, shifting the body from stress-response to rest-and-digest. The 396Hz frequency simultaneously dissolves mental blocks and fosters emotional liberation, helping you release the day and arrive at true calm.

────────────────────────────

\U0001f1ee\U0001f1f3 हिंदी में:
क्या आपका मन रात में शांत नहीं होता? राग दरबारी कनाडा 396Hz की उपचारक धुन सितार, बांसुरी और तबला के साथ आपके अतिसक्रिय मन को शांत करती है और गहरी नींद प्रदान करती है।
"अपने कोर्टिसोल को कम करें। अपनी साँसें धीमी करें। बाकी इस राग को करने दें।"

────────────────────────────

\U0001f49b If this music brought you stillness, please LIKE, SUBSCRIBE, and SHARE with someone who needs peace.
\U0001f514 Subscribe to DhunDetox for daily Indian classical healing music, raga therapy, and mindful sound journeys.
\U0001f4ac Comment below: What thoughts are you ready to release tonight?
\U0001f33f Save this video for when you need it most.

────────────────────────────

⚠️ Disclaimer: This music is intended for relaxation and wellness. Not a substitute for professional medical treatment.

#meditationmusic #indianclassicalmusic #healingmusic #stressrelief #sleepmusic #sitarmusic #ragamusic #soundhealing #ragatherapy #overthinking #dhundetox #राग_दरबारी #तनावमुक्ति #मनशांति #रात_की_शांति"""

youtube.videos().update(part='snippet', body={'id': 'bpk7tPoOhIs', 'snippet': {
    'title': 'When the New Week Feels Heavy \U0001f305 Raag Bhairavi 432Hz | Bansuri for Morning Cortisol',
    'description': bhairavi_desc, 'tags': bhairavi_tags, 'categoryId': '10',
}}).execute()
print('Bhairavi done.')

youtube.videos().update(part='snippet', body={'id': 'lLLBV_EMx_o', 'snippet': {
    'title': 'Overactive Mind? \U0001f319 Raag Darbari Kanada 396Hz | Sitar, Flute & Tabla for Midnight Calm',
    'description': darbari_desc, 'tags': darbari_tags, 'categoryId': '10',
}}).execute()
print('Darbari done.')
print('Both updated successfully.')
