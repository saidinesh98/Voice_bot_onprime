# stt.py - Multi-lingual version
from faster_whisper import WhisperModel
import numpy as np
from collections import Counter

# Unicode script ranges — 100% reliable for separating Indian/Arabic scripts
_SCRIPT_RANGES = [
    ('hi', 0x0900, 0x097F),  # Devanagari (Hindi)
    ('te', 0x0C00, 0x0C7F),  # Telugu
    ('ta', 0x0B80, 0x0BFF),  # Tamil
    ('ar', 0x0600, 0x06FF),  # Arabic
]

def detect_script(text: str):
    """Return language code if text is dominated by a non-Latin script, else None."""
    counts = {}
    for lang, lo, hi in _SCRIPT_RANGES:
        counts[lang] = sum(1 for c in text if lo <= ord(c) <= hi)
    best = max(counts, key=counts.get)
    # Need at least 3 characters of that script to be confident
    return best if counts[best] >= 3 else None


class STT:
    """Multi-lingual Speech-to-Text — focused on 6 languages."""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'ar': 'Arabic',
        'de': 'German',
    }

    def __init__(self, model_size='base'):
        print(f"Loading STT model ({model_size})...")
        self.model = WhisperModel(
            model_size,
            device='cpu',
            compute_type='int8',
            cpu_threads=8,
            num_workers=4
        )
        self.current_language = 'en'
        self.lang_history = []
        print("✅ STT ready")
        print(f"   Target languages: {', '.join(self.SUPPORTED_LANGUAGES.values())}")

    def transcribe(self, audio_np, detect_language=True):
        """Convert audio to text with language detection."""
        if audio_np is None or len(audio_np) < 8000:
            return "", self.current_language

        segments, info = self.model.transcribe(
            audio_np,
            beam_size=5,
            language=None if detect_language else self.current_language,
            # Short neutral prompt — does not bias language detection
            initial_prompt=".",
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=250,
                threshold=0.5
            )
        )

        # Collect transcript first so we can run script detection
        text = ' '.join(seg.text.strip() for seg in segments)

        whisper_lang = info.language if hasattr(info, 'language') else 'en'
        lang_prob = info.language_probability if hasattr(info, 'language_probability') else 1.0
        ALLOWED = set(self.SUPPORTED_LANGUAGES.keys())

        # --- LAYER 1: Unicode script detection (highest priority) ---
        # Telugu/Tamil/Hindi/Arabic scripts are mutually exclusive Unicode blocks.
        # If the transcribed text contains their characters, the language is certain.
        script_lang = detect_script(text)
        if script_lang:
            detected_lang = script_lang
            print(f"   [Script-detected: {self.SUPPORTED_LANGUAGES[script_lang]} ✓]")

        # --- LAYER 2: Whisper acoustic detection ---
        elif whisper_lang in ALLOWED and lang_prob >= 0.55:
            detected_lang = whisper_lang
            print(f"   [Whisper: {self.SUPPORTED_LANGUAGES.get(whisper_lang, whisper_lang)} ({lang_prob:.2f})]")

        elif whisper_lang not in ALLOWED and lang_prob >= 0.85:
            # High confidence detection of an UNSUPPORTED language (like Russian or Spanish)
            # We discard the text to prevent the bot from responding to the wrong language
            print(f"   [🛡️ Blocking unsupported language: {whisper_lang} ({lang_prob:.2f})]")
            return "", self.current_language

        else:
            # Low confidence or unsupported language — stay with current
            print(f"   [Low-confidence: whisper={whisper_lang} ({lang_prob:.2f}), keeping {self.current_language}]")
            detected_lang = self.current_language

        # --- CONSENSUS: require majority before switching ---
        if detect_language:
            self.lang_history.append(detected_lang)
            if len(self.lang_history) > 5:
                self.lang_history.pop(0)

            counts = Counter(self.lang_history)
            most_common, freq = counts.most_common(1)[0]
            # Script-detected languages switch faster (2/5) because they're certain
            threshold = 2 if script_lang else 3
            if freq >= threshold:
                self.current_language = most_common

        return text.strip(), self.current_language

    def transcribe_with_timestamp(self, audio_np):
        """Get transcription with word-level timestamps."""
        segments, _ = self.model.transcribe(audio_np, word_timestamps=True)
        words = []
        for segment in segments:
            for word in segment.words:
                words.append({
                    'word': word.word,
                    'start': word.start,
                    'end': word.end,
                    'probability': word.probability
                })
        return words


if __name__ == "__main__":
    stt = STT()
    print("\nTarget languages: English, Hindi, Tamil, Telugu, Arabic, German")
