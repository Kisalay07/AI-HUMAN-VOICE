"""
FastAPI Backend for The Empathy Engine.

Endpoints:
  POST /api/analyze     – Detect emotion from text
  POST /api/synthesize  – Detect emotion + generate modulated speech
  GET  /api/audio/{fn}  – Serve generated audio files
  GET  /                – Web UI
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import TextInput, EmotionResult
from app.emotion import EmotionDetector
from app.voice import VoiceModulator, OUTPUT_DIR

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="The Empathy Engine",
    description="AI voice synthesis with emotion-driven vocal modulation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for the web UI
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Singleton services
detector = EmotionDetector()
modulator = VoiceModulator()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_ui():
    """Serve the web interface."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/analyze", response_model=EmotionResult)
async def analyze_text(payload: TextInput):
    """Analyze text and return detected emotion + intensity."""
    try:
        result = detector.detect(payload.text)
        return EmotionResult(text=payload.text, **result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/synthesize")
async def synthesize_speech(payload: TextInput):
    """Detect emotion, modulate voice, and generate audio."""
    try:
        # Step 1: Detect emotion
        emotion_data = detector.detect(payload.text)

        emotion = emotion_data["emotion"]
        secondary_emotion = emotion_data.get("secondary_emotion")
        intensity = emotion_data["intensity"]

        # Step 2: Synthesize with modulated voice (run in thread to avoid blocking)
        loop = asyncio.get_event_loop()
        filepath, mod = await loop.run_in_executor(
            None,
            modulator.synthesize,
            payload.text, emotion, intensity, secondary_emotion
        )

        filename = os.path.basename(filepath)

        return {
            "emotion": {
                "text": payload.text,
                "emotion": emotion,
                "secondary_emotion": secondary_emotion,
                "intensity": intensity,
                "sentiment_scores": emotion_data["sentiment_scores"],
                "description": emotion_data["description"],
            },
            "voice_params": {
                "rate_change": mod["rate_change"],
                "pitch_change": mod["pitch_change"],
                "volume_change": mod["volume_change"],
                "emotion": emotion,
                "intensity": mod["intensity"],
            },
            "audio_url": f"/api/audio/{filename}",
            "filename": filename,
            "engine_used": "pyttsx3",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    """Serve a generated audio file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(filepath, media_type="audio/wav", filename=filename)


# ---------------------------------------------------------------------------
# Run with: uvicorn app.main:app --reload --port 8000
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
