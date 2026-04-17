import os
import json
import asyncio
import base64
import numpy as np
import io
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS

# Multi-lingual components
from multi_lingual.stt import STT
from multi_lingual.llm_client import LLMClient
from database_manager import DatabaseManager
from auth_utils import verify_token

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize multi-lingual components
print("\n📦 Loading Multi-lingual Models...")
stt = STT(model_size='small') # Multi-lingual model
llm = LLMClient(server_url="http://172.20.100.68:8000")
db = DatabaseManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # --- Keycloak Token Verification ---
    token = websocket.query_params.get("token")
    user_payload = verify_token(token)
    
    if not user_payload:
        print("❌ Unauthorized: Missing or invalid Keycloak token")
        # In some FastAPI versions, you must accept before closing with a code
        await websocket.accept()
        await websocket.close(code=4001) # Custom code for Unauthorized
        return

    await websocket.accept()
    user_name = user_payload.get("preferred_username", "Unknown User")
    print("\n" + "="*60)
    print(f"🚀  FRONTEND CONNECTED (User: {user_name})")
    print("="*60)
    
    audio_buffer = []
    is_listening = True
    
    try:
        while True:
            # Receive data from frontend
            try:
                message = await websocket.receive()
            except Exception:
                break
            
            # Check for disconnection
            if message.get("type") == "websocket.disconnect":
                break

            if "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "config":
                    print(f"⚙️  Config received: {data}")
                    continue
                if data.get("type") == "resume_listening":
                    print("\n🔄 Bot finished speaking. Resuming listening...")
                    is_listening = True
                    audio_buffer = [] # Clear any stale audio received while speaking
                    continue
            
            if "bytes" in message:
                if not is_listening:
                    continue
                    
                audio_chunk = message["bytes"]
                # Convert Int16 PCM to float32 for Whisper
                chunk_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                audio_buffer.append(chunk_np)
                
                # If we have enough audio (~1.2s), try to transcribe
                if len(audio_buffer) >= 6: 
                    full_audio = np.concatenate(audio_buffer)
                    
                    # Log that we are attempting transcription
                    if len(audio_buffer) % 10 == 0:
                        print(f"📡 Receiving audio... (buffer: {len(audio_buffer)} chunks)", end='\r')
                    
                    # Transcribe with auto language detection
                    text, detected_lang = stt.transcribe(full_audio, detect_language=True)
                    
                    if text and len(text.strip()) > 3:
                        print(f"\n📝 You [{detected_lang.upper()}]: {text}")
                        # Send transcription back to UI
                        await websocket.send_json({
                            "type": "transcription", 
                            "text": text,
                            "language": detected_lang
                        })

                        # --- Lead Capture Logic ---
                        # Clean text for phone detection (remove spaces)
                        clean_text = text.replace(" ", "")
                        phone_match = re.search(r'\d{10,12}', clean_text)
                        
                        # Name detection logic
                        name = None
                        name_match = re.search(r"(?:my name is|i am|this is)\s+([a-zA-Z]+)", text.lower())
                        if name_match:
                            name = name_match.group(1).capitalize()
                            
                        if phone_match or name:
                            phone = phone_match.group() if phone_match else None
                            # Check for project interest
                            interest = None
                            for project in ["SAMANA Hills", "SAMANA Palm Vista", "SAMANA Creek Horizon"]:
                                if project.lower() in text.lower():
                                    interest = project
                                    break
                            
                            # Save to PostgreSQL
                            db.add_lead(phone=phone, name=name, project=interest, raw_text=text)
                            print(f"📍 Database Update: Captured lead {name or 'User'} ({phone or 'No phone'}) for {interest or 'General'}")
                        # ---------------------------
                        
                        # Stop listening until bot finishes responding
                        is_listening = False
                        audio_buffer = []
                        
                        # Get LLM response and buffer it
                        print(f"🤔 Thinking in {detected_lang.upper()}...", end=' ', flush=True)
                        full_response = ""
                        for sentence in llm.stream_sentences(text, detected_lang):
                            if sentence and sentence.strip():
                                print(".", end='', flush=True)
                                full_response += sentence + " "
                                # Stream text to UI
                                await websocket.send_json({"type": "text", "text": sentence + " "})
                        
                        print(f"\n🤖 Bot [{detected_lang.upper()}]: {full_response.strip()}")
                        
                        # Generate TTS for the WHOLE response at once
                        if full_response.strip():
                            print(f"🔊 Generating speech in {detected_lang.upper()}...")
                            try:
                                # Map language codes for gTTS
                                lang_map = {
                                    'hi': 'hi', 'ta': 'ta', 'te': 'te', 'ml': 'ml', 'bn': 'bn',
                                    'ar': 'ar', 'en': 'en', 'fr': 'fr', 'de': 'de', 'es': 'es'
                                }
                                gtts_lang = lang_map.get(detected_lang, detected_lang[:2])
                                
                                tts_obj = gTTS(text=full_response.strip(), lang=gtts_lang)
                                mp3_fp = io.BytesIO()
                                tts_obj.write_to_fp(mp3_fp)
                                mp3_fp.seek(0)
                                
                                audio_b64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
                                await websocket.send_json({
                                    "type": "audio", 
                                    "data": audio_b64,
                                    "mimeType": "audio/mpeg"
                                })
                                print(f"✅ Speech sent to frontend\n")
                            except Exception as tts_err:
                                print(f"\n⚠️  TTS Error: {tts_err}")
                        
                        print(f"🔊 Speaking response...\n")
                        audio_buffer = [] 
                        
                    elif len(audio_buffer) > 100: # Max ~25 seconds of no transcription
                        # Slide window
                        audio_buffer = audio_buffer[20:] 
                        
    except WebSocketDisconnect:
        print("\n🔌 Frontend disconnected cleanly")
    except Exception as e:
        print(f"\n❌ Error in WebSocket: {e}")
    finally:
        print("🛑 Session ended\n")

# Serve static files from frontend/dist if they exist
frontend_dist = os.path.join("frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🌍 MULTI-LINGUAL SERVER STARTING AT: http://localhost:8001")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)
