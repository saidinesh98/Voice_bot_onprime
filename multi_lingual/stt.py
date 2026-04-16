# stt.py - Multi-lingual version
from faster_whisper import WhisperModel
import numpy as np

class STT:
    """Multi-lingual Speech-to-Text"""
    
    # Supported languages with their codes
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'ml': 'Malayalam',
        'kn': 'Kannada',
        'bn': 'Bengali',
        'mr': 'Marathi',
        'gu': 'Gujarati',
        'pa': 'Punjabi',
        'ur': 'Urdu',
        'fr': 'French',
        'de': 'German',
        'es': 'Spanish',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ru': 'Russian',
        'ar': 'Arabic'
    }
    
    def __init__(self, model_size='small'):  # Use 'small' for multi-lingual (not 'small.en')
        print(f"Loading multi-lingual STT model ({model_size})...")
        # Use multi-lingual model (supports 100+ languages)
        self.model = WhisperModel(
            model_size,  # 'small' supports multiple languages
            device='cpu',
            compute_type='int8',
            cpu_threads=4,
            num_workers=2
        )
        self.current_language = 'en'  # Default
        print("✅ Multi-lingual STT ready")
        print(f"   Supported languages: {len(self.SUPPORTED_LANGUAGES)}")
    
    def transcribe(self, audio_np, detect_language=True):
        """Convert audio to text with auto language detection"""
        if audio_np is None or len(audio_np) < 8000:
            return "", "en"
        
        # Transcribe with language detection
        segments, info = self.model.transcribe(
            audio_np,
            beam_size=3,
            language=None if detect_language else self.current_language,  # Auto-detect if None
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                threshold=0.5
            )
        )
        
        # Get detected language
        detected_lang = info.language if hasattr(info, 'language') else 'en'
        self.current_language = detected_lang
        
        # Combine all segments
        text = ' '.join(segment.text.strip() for segment in segments)
        
        # Get language name
        lang_name = self.SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)
        print(f"   [Detected: {lang_name}]")
        
        return text.strip(), detected_lang
    
    def transcribe_with_timestamp(self, audio_np):
        """Get transcription with word-level timestamps"""
        segments, _ = self.model.transcribe(
            audio_np,
            word_timestamps=True
        )
        
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

# Test
if __name__ == "__main__":
    stt = STT()
    print("\nTesting with different languages...")
    print("Speak in English, Hindi, Tamil, or any language")