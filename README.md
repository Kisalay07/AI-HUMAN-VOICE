# 🌟 The Empathy Engine: Giving AI a Human Voice

## 🎭 Project Overview

Standard Text-to-Speech (TTS) systems are highly functional but often lack the prosody, emotional range, and subtle vocal cues necessary to build genuine human connection. The empathy gap between text generation and audio delivery remains a challenge in automated interactions.

**The Empathy Engine** is a lightweight, offline-capable service designed to bridge the gap between text-based sentiment and expressive audio. It dynamically categorizes input text and programmatically modulates its acoustic delivery parameters based on the detected emotional context, creating a more human-like TTS experience.

---

## 🚀 Architecture and Tech Stack

The project prioritizes accessibility, performance, and offline capability without reliance on external API keys:

- **Python 3** — Core engine and application logic.
- **FastAPI** — High-performance async REST API framework.
- **VADER Sentiment** — Lexicon and rule-based sentiment analysis tool optimized for speed and social nuance.
- **pyttsx3** — Offline TTS engine utilizing native system voices (SAPI5 on Windows).
- **pydub** — Audio waveform post-processing for precise emotional audio effects.
- **Vanilla HTML/CSS/JS** — Responsive "Glassmorphism" frontend interface.

## 💡 Notes on Design Choices

*This section explains the logic used for mapping emotions to voice parameters, as requested in the deliverables.*

While `pyttsx3` is highly efficient for offline speech synthesis, its default output is notoriously monotonic. Furthermore, the default Windows reading voice operates at approximately 200 Words Per Minute (WPM), which is unusually fast for expressive dialogue. To fundamentally improve the acoustic output without relying on external APIs, the following architectural choices were made:

1. **Anchoring the Base Speed:** The baseline `pyttsx3` speaking rate was hardcoded down to **130 WPM** (a calm, deliberate pace). This was a critical design choice. By dropping the anchor speed significantly below the Windows default, percentage-based rate increases (e.g., +15% for "Excited") result in a naturally animated speaking pace rather than an unnatural, rushed effect.
2. **Dual-Layer Emotion Detection:** Sentiment analysis alone (Positive/Negative) is insufficient for nuanced emotional mapping. A two-layer system was implemented: VADER (for baseline polarity and compound scoring) combined with a heuristic Keyword Classifier to map sentences into 10 granular emotional states (e.g., *Surprised*, *Fearful*, *Inquisitive*). 
3. **Compound Modulations:** Every detected emotion adjusts native **Rate and Volume** while also applying `pydub` audio processing, such as injecting silence pauses before speech to simulate hesitation (for *Sad* or *Fearful*), or applying sharp volume fades (for *Angry*). Native Pydub pitch-shifting was deliberately avoided because resampling acoustic frames without a dedicated phase vocoder mathematically alters the temporal playback speed, causing undesirable distortion.
4. **Intensity Scaling:** The engine calculates an intensity score (0.0 to 1.0) derived from VADER heuristics and keyword density. A 0.2 intensity yields only partial modulation, whereas a 0.9 intensity pushes the acoustic modulation profiles to their maximum defined limits.
5. **Mixed Emotion Blending:** If an input sentence contains mixed heuristic signals (e.g., "I'm excited but surprised"), the engine detects both and linearly blends their vocal modulation profiles (70% primary variance, 30% secondary variance) to create complex acoustic tones.

---

## 🧠 Core Features & Modulations

### Emotion Mapping Logic

The voice engine utilizes predefined modulation profiles that scale linearly with detected intensity:

| Emotion | Rate | Volume | Post-Processing (Pydub Effects) |
|---|---|---|---|
| **Excited** | Faster (+15%) | Louder (+25%) | Sharp audio fade-in |
| **Sad** | Slower (-25%) | Quieter (-25%) | Pre/post silence pauses (hesitation), gentle wave fades |
| **Angry** | Faster (+10%) | Max Vol (+40%) | Sharp attack, zero hesitation |
| **Calm** | Slower (-20%) | Quieter (-15%) | Slower playback, smooth breath fades |

*Note: The engine dynamically attempts to select different underlying SAPI5 voices (e.g., higher-registered voices for sad/calm, lower-registered voices for angry/excited) if multiple distinct voice packs are available on the host operating system.*

---

## 🎮 Setup & Execution Instructions

All required configuration files are contained within this repository. No external API keys are needed.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Backend API Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Evaluate the Project
1. **Web Interface (Recommended):** Navigate to [http://localhost:8000](http://localhost:8000) in any modern web browser. Use the provided quick-fill chips (e.g., "Excited" or "Sad") and initiate the **Analyze & Speak** sequence. The frontend interface visually validates the intensity meter alongside playing the generated audio.
2. **CLI Interface:** Alternatively, open a separate terminal prompt and execute `python cli.py` for a colorized interactive terminal evaluation experience.

---

## 🏆 Functional Requirements Validation

| Requirement | Implementation Detail |
|---|---|
| **Text Input** | Fully supported via REST API (`/api/synthesize`), HTML textarea, and interactive CLI. |
| **Emotion Detection (3+ states)** | Categorizes sentences into **10** granular states using VADER polarity and keyword heuristics. |
| **Vocal Parameter Modulation** | Modulates native Rate, Volume, and Voice Type, alongside timeline/waveform effects. |
| **Emotion-to-Voice Mapping** | Achieved via a comprehensive programmatic mapping dictionary scaling linearly. |
| **Audio Output** | Procedurally generates standalone, playable `.wav` artifacts instantly. |

### 🌟 Bonus Objectives Validation
- ✅ **Granular Emotions:** Modeled 10 distinct emotional states successfully.
- ✅ **Intensity Scaling:** Developed a robust 0.0–1.0 intensity scalar that dynamically governs all vocal percentage alterations.
- ✅ **Web Interface:** Engineered a modern, fully-responsive frontend with real-time feedback, API linkage, and integrated HTML5 audio playback.
