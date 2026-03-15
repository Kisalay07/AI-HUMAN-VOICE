"""
Emotion Detection Module for The Empathy Engine.

Uses VADER sentiment analysis combined with keyword-based emotion classification
to detect granular emotions and their intensity from text input.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from typing import Tuple


# ---------------------------------------------------------------------------
# Keyword → Emotion mapping (lowercase stems / phrases)
# ---------------------------------------------------------------------------
EMOTION_KEYWORDS = {
    "happy": [
        "happy", "glad", "pleased", "delighted", "joyful", "cheerful",
        "wonderful", "fantastic", "great", "good", "nice", "love", "enjoy",
        "smile", "laugh", "blessed", "grateful", "thankful", "appreciate",
        "beautiful", "amazing", "awesome", "excellent", "brilliant", "perfect",
    ],
    "excited": [
        "excited", "thrilled", "ecstatic", "incredible", "unbelievable",
        "extraordinary", "phenomenal", "outstanding", "magnificent",
        "can't wait", "so pumped", "best ever", "blown away",
        "mind-blowing", "spectacular", "sensational", "electrifying",
    ],
    "sad": [
        "sad", "unhappy", "depressed", "miserable", "heartbroken",
        "disappointed", "unfortunate", "tragic", "terrible", "awful",
        "sorry", "regret", "miss", "lonely", "hopeless", "despair",
        "grief", "mourn", "cry", "tears", "painful", "suffering",
    ],
    "angry": [
        "angry", "furious", "outraged", "enraged", "livid", "irate",
        "frustrated", "annoyed", "irritated", "mad", "hate", "disgust",
        "unacceptable", "ridiculous", "absurd", "pathetic", "worst",
        "infuriating", "appalling", "disgusting", "fed up",
    ],
    "fearful": [
        "afraid", "scared", "terrified", "frightened", "anxious",
        "worried", "nervous", "panic", "dread", "horror", "alarmed",
        "uneasy", "tense", "threatened", "intimidated", "phobia",
    ],
    "surprised": [
        "surprised", "shocked", "astonished", "amazed", "stunned",
        "speechless", "unexpected", "wow", "whoa", "oh my", "no way",
        "unreal", "jaw-dropping", "startled", "flabbergasted",
    ],
    "concerned": [
        "concerned", "worried", "troubling", "disturbing", "alarming",
        "unsettling", "uncertain", "doubtful", "cautious", "wary",
        "issue", "problem", "risk", "warning", "careful",
    ],
    "inquisitive": [
        "why", "how", "what", "when", "where", "who", "which",
        "curious", "wondering", "question", "explain", "clarify",
        "understand", "know", "tell me", "interested", "inquire",
    ],
    "calm": [
        "calm", "peaceful", "serene", "relaxed", "tranquil", "quiet",
        "gentle", "soothing", "steady", "composed", "balanced",
        "mindful", "patient", "content", "comfortable", "at ease",
    ],
}


class EmotionDetector:
    """
    Detects emotion and intensity from text using a two-layer approach:
      1. VADER sentiment for polarity & intensity scoring.
      2. Keyword matching for granular emotion classification.
    """

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def detect(self, text: str) -> dict:
        """
        Analyse *text* and return a dict with:
          - emotion   : str   (e.g. "happy", "angry", "neutral")
          - intensity : float (0.0 – 1.0)
          - sentiment_scores : dict  (VADER raw scores)
          - description : str (human-readable explanation)
        """
        scores = self.analyzer.polarity_scores(text)
        # Find top 2 emotion keyword matches
        top_matches = self._keyword_match(text)
        
        keyword_emotion = "neutral"
        keyword_score = 0
        secondary_emotion = None
        
        if top_matches:
            keyword_emotion, keyword_score = top_matches[0]
            if len(top_matches) > 1 and top_matches[1][1] > 0:
                secondary_emotion = top_matches[1][0]

        vader_emotion = self._vader_to_emotion(scores)

        # Combine: keyword match wins when confident, else fall back to VADER
        if keyword_score >= 2:
            emotion = keyword_emotion
        elif keyword_score == 1 and keyword_emotion != "neutral":
            # Single keyword hit — prefer it only when VADER is weak
            if abs(scores["compound"]) < 0.3:
                emotion = keyword_emotion
            else:
                emotion = self._reconcile(keyword_emotion, vader_emotion, scores)
        else:
            emotion = vader_emotion

        # If primary and secondary are the same, clear secondary
        if secondary_emotion == emotion:
            secondary_emotion = None

        intensity = self._compute_intensity(scores, keyword_score)
        description = self._describe(emotion, intensity, scores, secondary_emotion)

        return {
            "emotion": emotion,
            "secondary_emotion": secondary_emotion,
            "intensity": round(intensity, 3),
            "sentiment_scores": {k: round(v, 4) for k, v in scores.items()},
            "description": description,
        }

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #
    def _keyword_match(self, text: str) -> list:
        """Return list of (emotion, match_count) sorted by highest hit count."""
        lower = text.lower()
        matches = []

        for emotion, keywords in EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', lower))
            if count > 0:
                matches.append((count, emotion))
                
        # Sort by count descending
        matches.sort(reverse=True)
        return [(e, c) for c, e in matches]

    def _vader_to_emotion(self, scores: dict) -> str:
        """Map VADER compound score to a basic emotion."""
        compound = scores["compound"]
        if compound >= 0.5:
            return "happy"
        elif compound >= 0.2:
            return "calm"
        elif compound <= -0.5:
            return "angry"
        elif compound <= -0.2:
            return "sad"
        return "neutral"

    def _reconcile(self, kw_emotion: str, vader_emotion: str, scores: dict) -> str:
        """When keyword and VADER disagree, pick the more specific one."""
        # Keyword emotions are more granular; prefer them if valence aligns
        positive_emotions = {"happy", "excited", "surprised", "calm"}
        negative_emotions = {"sad", "angry", "fearful", "concerned"}
        compound = scores["compound"]

        if kw_emotion in positive_emotions and compound > 0:
            return kw_emotion
        if kw_emotion in negative_emotions and compound < 0:
            return kw_emotion
        if kw_emotion == "inquisitive":
            return kw_emotion
        return vader_emotion

    def _compute_intensity(self, scores: dict, keyword_hits: int) -> float:
        """Compute 0-1 intensity from VADER magnitude + keyword density."""
        base = abs(scores["compound"])
        # Boost for multiple keyword hits (max boost 0.3)
        keyword_boost = min(keyword_hits * 0.1, 0.3)
        intensity = min(base + keyword_boost, 1.0)
        # Floor at 0.15 for non-neutral to ensure some modulation
        if intensity < 0.15 and scores["compound"] != 0:
            intensity = 0.15
        return intensity

    def _describe(self, emotion: str, intensity: float, scores: dict, secondary_emotion: str = None) -> str:
        """Human-readable description of the analysis."""
        strength = "strongly" if intensity > 0.7 else "moderately" if intensity > 0.4 else "mildly"
        base_desc = f"The text conveys a {strength} {emotion} tone"
        if secondary_emotion:
            base_desc += f", mixed with {secondary_emotion},"
        
        return (
            f"{base_desc} "
            f"(compound sentiment: {scores['compound']:.2f}, "
            f"intensity: {intensity:.1%})."
        )
