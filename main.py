#!/usr/bin/env python3
"""
Main Voice Bot - Fixed timing for TTS
"""
import sys
import time
import json
from english_one.audio_capture import AudioCapture
from english_one.stt import STT
from english_one.llm_client import LLMClient
from english_one.tts import TTS

def main():
    print("\n" + "="*60)
    print("🎙️  VOICE BOT - Windows (Fixed Timing)")
    print("="*60)
    
    print("\n📦 Initializing components...")
    
    try:
        mic = AudioCapture()
        stt = STT()
        llm = LLMClient(server_url="http://172.20.100.68:8000")
        tts = TTS()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    print("\n" + "="*60)
    print("✅ VOICE BOT READY")
    print("="*60)
    print("Speak into your microphone...")
    print("Say 'quit' to exit")
    print("-"*60 + "\n")
    
    # Welcome message
    welcome_msg = "Hello! I'm your AI assistant. How can I help you today?"
    print(f"🤖 {welcome_msg}")
    tts.speak(welcome_msg)
    time.sleep(0.5)  # Small delay after welcome
    
    while True:
        # Record audio
        audio = mic.record_utterance()
        if audio is None:
            continue
        
        # Transcribe
        print("Transcribing...", end=' ', flush=True)
        text = stt.transcribe(audio)
        print("done")
        
        if not text:
            error_msg = "I didn't catch that. Could you repeat?"
            print(f"🤖 {error_msg}")
            tts.speak(error_msg)
            time.sleep(0.3)
            continue
        
        print(f"\n📝 You: {text}")
        
        # Check for exit
        if text.lower() in ['quit', 'exit', 'goodbye', 'bye']:
            bye_msg = "Goodbye! Have a great day!"
            print(f"🤖 {bye_msg}")
            tts.speak(bye_msg)
            break
        
        # Clear memory command
        if 'clear memory' in text.lower() or 'clear history' in text.lower():
            llm.clear_history()
            clear_msg = "Conversation history cleared."
            print(f"🤖 {clear_msg}")
            tts.speak(clear_msg)
            time.sleep(0.3)
            continue
        
        # Get response from LLM
        print("🤔 Thinking...", end=' ', flush=True)
        full_response = ""
        
        try:
            # Collect the complete response
            for sentence in llm.stream_sentences(text):
                if sentence:
                    full_response += sentence + " "
                    print(".", end='', flush=True)
            
            print("\n")
            
            # Print and speak the response
            if full_response.strip():
                response_text = full_response.strip()
                print(f"🤖 Bot: {response_text}")
                
                # IMPORTANT: Release audio device and add delay
                time.sleep(0.5)  # Critical: Give time for recording to fully stop
                
                # Speak the response
                print(f"🔊 Speaking response...")
                tts.speak(response_text)
                time.sleep(0.3)  # Small pause after speaking
                
            else:
                error_msg = "Sorry, I couldn't generate a response."
                print(f"🤖 {error_msg}")
                time.sleep(0.3)
                tts.speak(error_msg)
                
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {e}"
            print(f"\n❌ {error_msg}")
            time.sleep(0.3)
            tts.speak("Sorry, I encountered an error. Please try again.")
        
        print()  # Empty line

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("Press Enter to exit...")