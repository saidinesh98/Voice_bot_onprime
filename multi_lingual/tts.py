# tts.py - Now supports Hindi and other languages via gTTS
import win32com.client
import pythoncom
import time
import io
import os

class TTS:
    """Multi-language TTS - English uses Windows voices, others use gTTS"""
    
    # Languages that should use gTTS (not natively supported by Windows)
    USE_GTTS_LANGUAGES = ['hi', 'ta', 'te', 'ml', 'bn', 'ar', 'ar-eg', 'ar-sa', 'fr', 'de', 'es', 'zh', 'ja', 'ru']
    
    def __init__(self):
        # Setup offline TTS for English
        try:
            pythoncom.CoInitialize()
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            self.speaker.Rate = 1
            self.speaker.Volume = 100
            self.offline_available = True
            print("✅ English TTS ready (Windows voices)")
        except Exception as e:
            print(f"⚠️  Windows TTS unavailable: {e}")
            self.offline_available = False
        
        # Setup gTTS for other languages
        try:
            from gtts import gTTS
            import pygame
            self.gTTS = gTTS
            pygame.mixer.init()
            self.online_available = True
            print("✅ Multi-language TTS ready (gTTS for Hindi, Tamil, Arabic, etc.)")
        except ImportError as e:
            print(f"⚠️  gTTS not available: {e}")
            print("   Run: pip install gtts pygame")
            self.online_available = False
    
    def speak(self, text, language='en'):
        """Speak text in specified language"""
        if not text or not text.strip():
            return
        
        print(f"🔊 [{language.upper()}] {text[:100]}...")
        
        # For English, use Windows voice (offline, fast)
        if language == 'en' and self.offline_available:
            self._speak_offline(text)
        
        # For Hindi and other languages, use gTTS
        elif language in self.USE_GTTS_LANGUAGES and self.online_available:
            self._speak_online(text, language)
        
        # Fallback: try gTTS for anything else
        elif self.online_available:
            self._speak_online(text, language)
        
        # Last resort: use English voice
        elif self.offline_available:
            print(f"   (Speaking in English instead)")
            self._speak_offline(f"In {language}: {text[:80]}")
        
        else:
            print(f"   [NO TTS] {text}")
    
    def _speak_offline(self, text):
        """Use Windows SAPI (English only)"""
        try:
            self.speaker.Speak(text)
        except Exception as e:
            print(f"   ⚠️  Windows TTS error: {e}")
    
    def _speak_online(self, text, language='hi'):
        """Use Google TTS for any language"""
        try:
            from gtts import gTTS
            import pygame
            
            # Map language codes to gTTS format
            lang_map = {
                'hi': 'hi',      # Hindi
                'ta': 'ta',      # Tamil
                'te': 'te',      # Telugu
                'ml': 'ml',      # Malayalam
                'bn': 'bn',      # Bengali
                'ar': 'ar',      # Arabic
                'ar-eg': 'ar',   # Egyptian Arabic
                'ar-sa': 'ar',   # Saudi Arabic
                'fr': 'fr',      # French
                'de': 'de',      # German
                'es': 'es',      # Spanish
                'zh': 'zh-CN',   # Chinese
                'ja': 'ja',      # Japanese
                'ru': 'ru',      # Russian
                'en': 'en'       # English (fallback)
            }
            
            gtts_lang = lang_map.get(language, language[:2])
            
            # Create speech
            tts = self.gTTS(text=text, lang=gtts_lang, slow=False)
            
            # Save to memory and play
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
        except Exception as e:
            print(f"   ⚠️  gTTS error: {e}")
            # Fallback to English
            if self.offline_available:
                self._speak_offline(f"Unable to speak in {language}. Message: {text[:80]}")
    
    def stop(self):
        """Stop any ongoing speech"""
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass
        try:
            self.speaker.Skip("Sentence")
        except:
            pass

# Test function
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing TTS with multiple languages")
    print("="*50 + "\n")
    
    tts = TTS()
    
    # Test English
    print("1. Testing English...")
    tts.speak("Hello, this is English test", 'en')
    time.sleep(1)
    
    # Test Hindi
    print("\n2. Testing Hindi...")
    tts.speak("नमस्ते, यह हिंदी टेस्ट है। मैं हिंदी में बोल रहा हूँ।", 'hi')
    time.sleep(2)
    
    # Test Tamil
    print("\n3. Testing Tamil...")
    tts.speak("வணக்கம், இது தமிழ் சோதனை. நான் தமிழில் பேசுகிறேன்.", 'ta')
    time.sleep(2)
    
    # Test Arabic
    print("\n4. Testing Arabic...")
    tts.speak("مرحباً، هذا اختبار باللغة العربية", 'ar')
    
    print("\n" + "="*50)
    print("✅ TTS Test Complete!")
    print("="*50)