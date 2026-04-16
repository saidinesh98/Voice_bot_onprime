# diagnose_tts.py - Comprehensive TTS diagnostic
import pyttsx3
import sys

print("="*60)
print("Windows TTS Diagnostic")
print("="*60)

# Test 1: Basic pyttsx3
print("\n1. Testing pyttsx3...")
try:
    engine = pyttsx3.init()
    print("   ✅ Engine initialized")
    
    # Get properties
    rate = engine.getProperty('rate')
    volume = engine.getProperty('volume')
    voices = engine.getProperty('voices')
    print(f"   Rate: {rate}")
    print(f"   Volume: {volume}")
    print(f"   Voices available: {len(voices)}")
    
    for voice in voices:
        print(f"     - {voice.name}")
    
    # Try to speak
    print("\n   Attempting to speak...")
    engine.say("This is a test of the text to speech system.")
    engine.runAndWait()
    print("   ✅ Speak command completed")
    print("   ❓ Did you hear audio?")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Using Windows PowerShell
print("\n2. Testing Windows PowerShell TTS...")
import subprocess
powershell_cmd = '''
Add-Type -AssemblyName System.Speech
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speech.Speak("Hello from PowerShell")
'''
try:
    result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                          capture_output=True, text=True, timeout=10)
    print("   ✅ PowerShell TTS command executed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Check Windows audio
print("\n3. Audio System Check:")
print("   Please check:")
print("   - Speakers/headphones are connected")
print("   - Volume is not muted")
print("   - Windows is not using a different output device")
print("   - Try playing a YouTube video or music to test")

print("\n" + "="*60)
input("Press Enter after checking audio...")