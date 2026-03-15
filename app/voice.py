"""
Voice Modulation & TTS Module for The Empathy Engine.

Uses pyttsx3 (offline, as suggested in the assignment) for TTS synthesis.
Modulates rate, pitch, and volume based on detected emotion and intensity.
Post-processes audio with pydub for pitch shifting and emotional effects.
"""

import os
import uuid
import pyttsx3
from pydub import AudioSegment
from pydub.effects import speedup
from typing import Dict, Tuple


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Emotion → Voice Modulation Profiles
# Each profile: (rate_delta%, pitch_delta%, volume_delta%)
# Values are MAXIMUM deltas — actual values are scaled by intensity (0-1).
# More dramatic values to create clearly distinguishable emotional voices.
# ---------------------------------------------------------------------------
MODULATION_PROFILES: Dict[str, Tuple[float, float, float]] = {
    # (rate%, pitch%, volume%)
    # Pitch is set to 0 as pure offline pydub pitch-shifting inextricably alters playback speed.
    "happy":       ( +5,  0, +15), 
    "excited":     (+15,  0, +25),
    "sad":         (-25,  0, -25),
    "angry":       (+10,  0, +40),
    "fearful":     ( +5,  0, -20),
    "surprised":   (+10,  0, +25),
    "concerned":   (-10,  0,  -5),
    "inquisitive": ( +0,  0,   0),
    "calm":        (-20,  0, -15),
    "neutral":     (  0,  0,   0),
}

# ---------------------------------------------------------------------------
# Emotion → extra audio effects for realism
#   pause_before_ms : silence before speech (hesitation, e.g. fearful/sad)
#   pause_after_ms  : trailing silence
#   speed_factor    : additional pydub speed tweak (1.0 = normal)
# ---------------------------------------------------------------------------
EMOTION_EFFECTS: Dict[str, dict] = {
    "happy":       {"pause_before_ms": 0,   "pause_after_ms": 0,   "speed_factor": 1.0},
    "excited":     {"pause_before_ms": 0,   "pause_after_ms": 0,   "speed_factor": 1.0},
    "sad":         {"pause_before_ms": 400, "pause_after_ms": 300, "speed_factor": 0.92},
    "angry":       {"pause_before_ms": 0,   "pause_after_ms": 0,   "speed_factor": 1.06},
    "fearful":     {"pause_before_ms": 300, "pause_after_ms": 200, "speed_factor": 1.0},
    "surprised":   {"pause_before_ms": 200, "pause_after_ms": 0,   "speed_factor": 1.02},
    "concerned":   {"pause_before_ms": 200, "pause_after_ms": 100, "speed_factor": 0.96},
    "inquisitive": {"pause_before_ms": 100, "pause_after_ms": 0,   "speed_factor": 1.0},
    "calm":        {"pause_before_ms": 200, "pause_after_ms": 200, "speed_factor": 0.94},
    "neutral":     {"pause_before_ms": 0,   "pause_after_ms": 0,   "speed_factor": 1.0},
}


class VoiceModulator:
    """
    Maps emotion + intensity to vocal parameters and generates audio.
    Uses pyttsx3 for synthesis + pydub for post-processing to create
    human-like emotional variation in speech.
    """

    def __init__(self):
        # Discover available SAPI5 voices on this system
        engine = pyttsx3.init()
        self._available_voices = engine.getProperty("voices")
        engine.stop()

    # ------------------------------------------------------------------ #
    # Parameter calculation
    # ------------------------------------------------------------------ #
    def get_modulation(self, emotion: str, intensity: float, secondary_emotion: str = None) -> dict:
        """
        Return a dict describing the vocal modulation that will be applied.
        If a secondary emotion exists, blend the parameters (70% primary, 30% secondary).
        """
        profile = MODULATION_PROFILES.get(emotion, (0, 0, 0))
        rate_base, pitch_base, vol_base = profile
        
        if secondary_emotion and secondary_emotion in MODULATION_PROFILES:
            profile_sec = MODULATION_PROFILES[secondary_emotion]
            rate_base = (rate_base * 0.7) + (profile_sec[0] * 0.3)
            pitch_base = (pitch_base * 0.7) + (profile_sec[1] * 0.3)
            vol_base = (vol_base * 0.7) + (profile_sec[2] * 0.3)

        rate_delta  = rate_base * intensity
        pitch_delta = pitch_base * intensity
        vol_delta   = vol_base * intensity

        return {
            "rate_change":   f"{rate_delta:+.1f}%",
            "pitch_change":  f"{pitch_delta:+.1f}%",
            "volume_change": f"{vol_delta:+.1f}%",
            "emotion": emotion,
            "intensity": round(intensity, 3),
            # raw numeric values for internal use
            "_rate":  rate_delta,
            "_pitch": pitch_delta,
            "_vol":   vol_delta,
        }

    # ------------------------------------------------------------------ #
    # Voice selection — pick different voices for different emotions
    # ------------------------------------------------------------------ #
    def _pick_voice(self, emotion: str):
        """
        Try to pick a suitable SAPI5 voice for the emotion.
        On Windows, there are often multiple voices (e.g. David, Zira, Mark).
        Using different voices for different emotions adds variety.
        """
        voices = self._available_voices
        if not voices or len(voices) < 2:
            return None  # stick with default

        # Try to find voice names
        voice_names = [(v.id, v.name.lower() if v.name else "") for v in voices]

        # Use a softer / female voice for sad, fearful, calm, concerned
        soft_emotions = {"sad", "fearful", "calm", "concerned"}
        # Use a stronger / male voice for angry, excited
        strong_emotions = {"angry", "excited"}

        if emotion in soft_emotions:
            # Prefer Zira or any female voice
            for vid, vname in voice_names:
                if "zira" in vname or "female" in vname or "eva" in vname:
                    return vid
        elif emotion in strong_emotions:
            # Prefer David or any male voice
            for vid, vname in voice_names:
                if "david" in vname or "male" in vname or "mark" in vname:
                    return vid

        return None  # use default

    # ------------------------------------------------------------------ #
    # Core synthesis with pyttsx3 + pydub post-processing
    # ------------------------------------------------------------------ #
    def synthesize(self, text: str, emotion: str, intensity: float, secondary_emotion: str = None) -> Tuple[str, dict]:
        """
        Generate emotionally expressive speech:
          1. pyttsx3 sets rate & volume natively
          2. pydub shifts pitch by resampling
          3. pydub adds emotional effects (pauses, speed tweaks)
        Returns (filepath, modulation_dict).
        """
        mod = self.get_modulation(emotion, intensity, secondary_emotion)
        filename = f"empathy_{uuid.uuid4().hex[:8]}.wav"
        raw_path = os.path.join(OUTPUT_DIR, f"_raw_{filename}")
        final_path = os.path.join(OUTPUT_DIR, filename)

        # Fresh engine each call to avoid COM threading issues on Windows
        engine = pyttsx3.init()

        # --- Voice selection ---
        chosen_voice = self._pick_voice(emotion)
        if chosen_voice:
            engine.setProperty("voice", chosen_voice)

        # --- Rate ---
        # Windows pyttsx3 default rate is 200 WPM, which is naturally VERY fast.
        # We explicitly anchor the baseline to 130 WPM (a slow, deliberate speaking pace).
        base_rate = 130
        
        # Calculate new rate directly using the percentage
        new_rate = int(base_rate * (1 + mod["_rate"] / 100))
        new_rate = max(80, min(new_rate, 400))  # clamp
        engine.setProperty("rate", new_rate)

        # --- Volume ---
        base_vol = engine.getProperty("volume")  # 0.0 – 1.0
        new_vol = base_vol * (1 + mod["_vol"] / 100)
        new_vol = max(0.1, min(new_vol, 1.0))
        engine.setProperty("volume", new_vol)

        # Save to WAV
        engine.save_to_file(text, raw_path)
        engine.runAndWait()
        engine.stop()

        # --- Post-processing with pydub ---
        try:
            audio = AudioSegment.from_wav(raw_path)
            # Note: Pitch shifting via frame_rate manipulation in pydub inextricably alters playback speed,
            # resulting in an unnatural chipmunk effect. We rely exclusively on Native Rate + Volume + Pydub fades/pauses.
            audio = self._apply_emotion_effects(audio, emotion, intensity)
            audio.export(final_path, format="wav")
        except Exception:
            # If post-processing fails, use raw file
            if os.path.exists(raw_path):
                if os.path.exists(final_path):
                    os.remove(final_path)
                os.rename(raw_path, final_path)

        # Cleanup raw file
        if os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except OSError:
                pass

        return final_path, mod

    # ------------------------------------------------------------------ #
    # Audio post-processing helpers

    def _apply_emotion_effects(self, audio: AudioSegment, emotion: str, intensity: float) -> AudioSegment:
        """
        Apply emotion-specific audio effects to make speech sound
        more human-like and emotionally distinct:
          - Pauses (hesitation for sad/fearful, breath for calm)
          - Speed tweaks for energy level
          - Volume fade effects
        """
        effects = EMOTION_EFFECTS.get(emotion, {})
        if not effects:
            return audio

        # Scale effects by intensity
        pause_before = int(effects.get("pause_before_ms", 0) * intensity)
        pause_after = int(effects.get("pause_after_ms", 0) * intensity)
        speed = effects.get("speed_factor", 1.0)

        # Blend speed toward 1.0 based on intensity (full effect at intensity=1)
        speed = 1.0 + (speed - 1.0) * intensity

        # Apply speed change
        if speed > 1.01:
            try:
                audio = speedup(audio, playback_speed=speed)
            except Exception:
                pass  # speedup can fail on very short clips
        elif speed < 0.99:
            # Slow down by adjusting frame rate then resampling
            slow_rate = int(audio.frame_rate * speed)
            slow_rate = max(8000, slow_rate)
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": slow_rate
            })
            audio = audio.set_frame_rate(44100)

        # Add silence pauses for emotional effect
        if pause_before > 0:
            silence_before = AudioSegment.silent(duration=pause_before)
            audio = silence_before + audio

        if pause_after > 0:
            silence_after = AudioSegment.silent(duration=pause_after)
            audio = audio + silence_after

        # Fade effects for certain emotions
        if emotion == "sad":
            # Gentle fade-in and fade-out for melancholy feel
            fade_len = min(300, len(audio) // 4)
            audio = audio.fade_in(fade_len).fade_out(fade_len)
        elif emotion == "angry":
            # Sharp attack — very short fade-in
            audio = audio.fade_in(50)
        elif emotion == "calm":
            # Smooth fades for soothing feel
            fade_len = min(400, len(audio) // 3)
            audio = audio.fade_in(fade_len).fade_out(fade_len)
        elif emotion in ("excited", "surprised"):
            # Quick fade-in to simulate burst of energy
            audio = audio.fade_in(80)

        return audio
