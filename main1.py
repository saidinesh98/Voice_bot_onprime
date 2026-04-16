# main.py - Multi-lingual voice bot
import sys
import time
import json
from multi_lingual.audio_capture import AudioCapture
from multi_lingual.stt import STT
from multi_lingual.llm_client import LLMClient
from multi_lingual.tts import TTS

def main():
    print("\n" + "="*60)
    print("🌍 MULTI-LINGUAL VOICE BOT")
    print("="*60)
    print("Supported Languages: English, Hindi, Tamil, Telugu, Malayalam, Bengali")
    print("Speak naturally - bot will auto-detect your language!")
    print("="*60)
    
    # Initialize components
    print("\n📦 Loading models...")
    mic = AudioCapture()
    stt = STT()  # Multi-lingual model
    llm = LLMClient(server_url="http://172.20.100.68:8000")
    tts = TTS()  # Multi-lingual TTS
    
    print("\n" + "="*60)
    print("✅ BOT READY")
    print("="*60)
    print("Speak in any supported language...")
    print("Say 'quit' to exit, 'clear' to clear memory")
    print("-"*60 + "\n")
    
    # Welcome in multiple languages
    welcome_msg = "Hello! I can speak multiple languages. Try English, Hindi, or Tamil!"
    print(f"🤖 {welcome_msg}")
    tts.speak(welcome_msg, 'en')
    
    while True:
        # Record audio
        audio = mic.record_utterance()
        if audio is None:
            continue
        
        # Transcribe with auto language detection
        print("Transcribing...", end=' ', flush=True)
        text, detected_lang = stt.transcribe(audio, detect_language=True)
        print("done")
        
        if not text:
            msg = "I didn't catch that. Could you repeat?"
            print(f"🤖 {msg}")
            tts.speak(msg, 'en')
            continue
        
        print(f"\n📝 You [{detected_lang.upper()}]: {text}")
        
        # Check commands
        if text.lower() in ['quit', 'exit', 'goodbye', 'bye', 'बाय', 'விடை']:
            bye_msg = "Goodbye! Have a great day!"
            print(f"🤖 {bye_msg}")
            tts.speak(bye_msg, 'en')
            break
        
        if 'clear' in text.lower() or 'साफ' in text:
            llm.clear_history(detected_lang)
            msg = "Conversation history cleared."
            print(f"🤖 {msg}")
            tts.speak(msg, 'en')
            continue
        
        # Get response in same language
        print(f"🤔 Thinking in {detected_lang.upper()}...", end=' ', flush=True)
        full_response = ""
        
        for sentence in llm.stream_sentences(text, detected_lang):
            if sentence:
                full_response += sentence + " "
                print(".", end='', flush=True)
        
        print("\n")
        
        if full_response.strip():
            response_text = full_response.strip()
            print(f"🤖 Bot [{detected_lang.upper()}]: {response_text}")
            time.sleep(0.3)
            tts.speak(response_text, detected_lang)
        else:
            msg = "Sorry, I couldn't generate a response."
            print(f"🤖 {msg}")
            tts.speak(msg, 'en')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")