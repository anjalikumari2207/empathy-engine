# 🎙 Empathy Engine

> *An AI-powered Text-to-Speech service that detects the emotion in your words — and speaks them that way.*

---

## What It Does

Type any sentence. The Empathy Engine:
1. **Analyzes the emotion** using VADER sentiment analysis + a custom keyword lexicon
2. **Classifies it** into one of 8 emotional states (Happy, Excited, Sad, Angry, Fearful, Surprised, Concerned, Neutral)
3. **Scales the intensity** (Low / Medium / High) based on punctuation, capitalization, and keyword strength
4. **Modulates the voice** — adjusting **rate**, **pitch**, and **volume** using gTTS + pydub
5. **Delivers a `.mp3` file** you can play or download

---

## Features

| Feature | Status |
|---|---|
| 3+ emotion categories (8 total) | ✅ |
| 2+ vocal parameters (rate + pitch + volume) | ✅ |
| Audio output (.mp3) | ✅ |
| Intensity scaling (low / base / high) | ✅ Bonus |
| Granular emotion detection | ✅ Bonus |
| Web UI with embedded audio player | ✅ Bonus |

---

## Architecture

```
empathy-engine/
├── app.py              # Flask server + API routes
├── emotion_engine.py   # Emotion detection & voice mapping
├── voice_engine.py     # gTTS synthesis + pydub modulation
├── requirements.txt
├── templates/
│   └── index.html      # Single-page web interface
└── static/
    ├── css/style.css
    ├── js/app.js
    └── audio/          # Generated audio files (auto-created)
```

---

## Setup & Run

### 1. Clone / unzip the repo

```bash
git clone <your-repo-url>
cd empathy-engine
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `pydub` requires `ffmpeg` for MP3 output.
> - **macOS:** `brew install ffmpeg`
> - **Ubuntu/Debian:** `sudo apt-get install ffmpeg`
> - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### 4. Run the server

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## API

### `POST /api/synthesize`

**Request body:**
```json
{ "text": "I just won the championship! This is incredible!!" }
```

**Response:**
```json
{
  "audio_url": "/static/audio/audio_abc123.mp3",
  "emotion": "excited",
  "confidence": 91.5,
  "intensity": "high",
  "voice_params": {
    "rate": 1.5,
    "pitch": "+12st",
    "volume": 100
  },
  "scores": {
    "excited": 0.52,
    "happy": 0.23,
    "surprised": 0.10,
    ...
  }
}
```

---

## Design Choices

### Emotion Detection
Rather than relying solely on positive/negative sentiment (too coarse), the engine combines:
- **VADER** for compound sentiment as a fallback baseline
- **Custom keyword lexicon** with per-emotion word lists and weights
- **Punctuation signals** (`!` boosts excited/angry/surprised, `?` boosts surprised)
- **Capitalization ratio** (lots of CAPS → higher intensity)

This gives 8 distinct emotional states without needing a heavy ML model.

### Emotion → Voice Mapping

Each emotion has a 3-tier voice profile (low / base / high intensity):

| Emotion | Rate | Pitch | Volume |
|---|---|---|---|
| Excited | 1.35–1.5× | +8 to +12st | 95–100% |
| Happy | 1.0–1.2× | +2 to +6st | 85–92% |
| Angry | 1.1–1.3× | −1 to −4st | 92–100% |
| Sad | 0.75–0.88× | −3 to −7st | 65–78% |
| Fearful | 0.95–1.15× | +1 to +5st | 70–80% |
| Surprised | 1.05–1.25× | +3 to +9st | 85–95% |
| Concerned | 0.85–0.95× | −1 to −3st | 78–82% |
| Neutral | 1.0× | 0st | 85% |

### Audio Modulation
`voice_engine.py` uses a pure-Python approach without external ML:
- **Speed:** Frame-rate manipulation on the raw PCM data (no re-encoding artifacts)
- **Pitch shift:** Frame-rate trick + inverse speed correction (preserves duration while shifting pitch)
- **Volume:** dBFS normalization to a target level

This avoids heavyweight libraries and works fully offline after install.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python + Flask | Simple, fast to iterate |
| Emotion Analysis | VADER + keyword lexicon | No GPU needed, fast, explainable |
| TTS | gTTS (Google TTS) | Natural voice; falls back to pyttsx3 offline |
| Audio processing | pydub | Clean API for rate/pitch/volume |
| Frontend | Vanilla HTML/CSS/JS | No build step; zero dependencies |

---

## License

MIT
