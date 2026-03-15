"""
Pydantic data models for The Empathy Engine.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict


class TextInput(BaseModel):
    """Input model for text analysis and synthesis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze and synthesize")


class EmotionResult(BaseModel):
    """Result of emotion analysis."""
    text: str
    emotion: str
    secondary_emotion: Optional[str] = None
    intensity: float = Field(..., ge=0.0, le=1.0)
    sentiment_scores: Dict[str, float]
    description: str


class VoiceParameters(BaseModel):
    """Vocal modulation parameters applied to TTS."""
    rate_change: str
    pitch_change: str
    volume_change: str
    emotion: str
    intensity: float


class SynthesisResult(BaseModel):
    """Result of voice synthesis."""
    emotion: EmotionResult
    voice_params: VoiceParameters
    audio_url: str
    filename: str
    engine_used: str
