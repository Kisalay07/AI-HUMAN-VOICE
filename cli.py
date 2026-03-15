"""
CLI Interface for The Empathy Engine.

Interactive command-line tool to analyze text emotions and generate
expressive speech audio files.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.emotion import EmotionDetector
from app.voice import VoiceModulator, OUTPUT_DIR


# ---------------------------------------------------------------------------
# ANSI Colors for pretty terminal output
# ---------------------------------------------------------------------------
class Colors:
    HEADER   = "\033[95m"
    BLUE     = "\033[94m"
    CYAN     = "\033[96m"
    GREEN    = "\033[92m"
    YELLOW   = "\033[93m"
    RED      = "\033[91m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    RESET    = "\033[0m"


EMOTION_COLORS = {
    "happy":       Colors.GREEN,
    "excited":     Colors.YELLOW,
    "sad":         Colors.BLUE,
    "angry":       Colors.RED,
    "fearful":     Colors.RED,
    "surprised":   Colors.YELLOW,
    "concerned":   Colors.YELLOW,
    "inquisitive": Colors.CYAN,
    "calm":        Colors.CYAN,
    "neutral":     Colors.DIM,
}


def print_banner():
    """Print the startup banner."""
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════╗
║           🎙️  THE EMPATHY ENGINE  🎙️                ║
║     AI Voice Synthesis with Emotion Detection        ║
╚══════════════════════════════════════════════════════╝{Colors.RESET}
{Colors.DIM}  Engine: pyttsx3 (offline)
  Type 'quit' to exit{Colors.RESET}
""")


def print_result(emotion_data: dict, mod: dict, filepath: str):
    """Pretty-print the analysis and synthesis results."""
    emotion = emotion_data["emotion"]
    intensity = emotion_data["intensity"]
    color = EMOTION_COLORS.get(emotion, Colors.RESET)

    bar_len = int(intensity * 20)
    bar = "█" * bar_len + "░" * (20 - bar_len)

    print(f"""
{Colors.BOLD}┌─── Analysis Result ───────────────────────────┐{Colors.RESET}
│  Emotion:    {color}{Colors.BOLD}{emotion.upper()}{Colors.RESET}
│  Intensity:  [{bar}] {intensity:.1%}
│  Sentiment:  pos={emotion_data['sentiment_scores']['pos']:.3f}  neg={emotion_data['sentiment_scores']['neg']:.3f}  neu={emotion_data['sentiment_scores']['neu']:.3f}
│
│  {Colors.DIM}{emotion_data['description']}{Colors.RESET}
│
{Colors.BOLD}├─── Voice Modulation ──────────────────────────┤{Colors.RESET}
│  Rate:     {mod['rate_change']:>8s}
│  Pitch:    {mod['pitch_change']:>8s}
│  Volume:   {mod['volume_change']:>8s}
│  Engine:   pyttsx3
│
│  📁 Audio: {Colors.CYAN}{filepath}{Colors.RESET}
{Colors.BOLD}└───────────────────────────────────────────────┘{Colors.RESET}
""")


def main():
    """Run the interactive CLI."""
    print_banner()

    detector = EmotionDetector()
    modulator = VoiceModulator()

    while True:
        try:
            text = input(f"{Colors.BOLD}{Colors.GREEN}Enter text ▶ {Colors.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.DIM}Goodbye! 👋{Colors.RESET}")
            break

        if not text:
            continue
        if text.lower() == "quit":
            print(f"{Colors.DIM}Goodbye! 👋{Colors.RESET}")
            break

        # Analyze
        emotion_data = detector.detect(text)

        # Synthesize
        print(f"{Colors.DIM}  Generating speech...{Colors.RESET}", end="", flush=True)
        try:
            filepath, mod = modulator.synthesize(
                text,
                emotion_data["emotion"],
                emotion_data["intensity"],
            )
            print(f"\r{' ' * 40}\r", end="")
            print_result(emotion_data, mod, filepath)
        except Exception as e:
            print(f"\r{Colors.RED}  Error: {e}{Colors.RESET}\n")


if __name__ == "__main__":
    main()
