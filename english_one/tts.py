# tts.py - Using win32com (Windows native)
import win32com.client
import pythoncom
import time

class TTS:
    def __init__(self):
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            # Create SAPI voice
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Configure
            self.speaker.Rate = 1  # Speed: -10 to 10
            self.speaker.Volume = 100
            
            # Test
            print("✅ Windows SAPI TTS ready")
            self.backend = 'sapi'
        except Exception as e:
            print(f"❌ TTS init error: {e}")
            self.backend = 'none'
    
    def speak(self, text):
        if not text or not text.strip():
            return
        
        print(f"🔊 SPEAKING: {text}")
        
        if self.backend == 'sapi':
            try:
                # Speak synchronously
                self.speaker.Speak(text)
                print("   ✅ Done")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   No TTS backend")
    
    def __del__(self):
        try:
            pythoncom.CoUninitialize()
        except:
            pass

# Test
if __name__ == "__main__":
    tts = TTS()
    tts.speak("Hello, this is a test")
    time.sleep(1)
    tts.speak("Can you hear me?")