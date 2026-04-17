import os
import json
import asyncio
import base64
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from english_one.stt import STT
from english_one.llm_client import LLMClient
from gtts import gTTS
import io

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
# Using low model size for faster local processing
stt = STT()
# VM LLM Server
llm = LLMClient(server_url="http://172.20.100.68:8000")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("\n" + "="*60)
    print("🚀  FRONTEND CONNECTED")
    print("="*60)
    audio_buffer = []
    is_listening = True
    
    try:
        while True:
            # Receive data from frontend
            try:
                message = await websocket.receive()
            except Exception:
                # Handle cases where connection is already closed
                break
            
            # Check for disconnection
            if message.get("type") == "websocket.disconnect":
                print("\n🔌 Frontend disconnected")
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
                
                # Pulse log to show audio is coming in
                if len(audio_buffer) % 5 == 0:
                    print(f"📡 Receiving audio... (buffer: {len(audio_buffer)} chunks | {len(audio_buffer)*0.25:.1f}s)", end='\r')
                
                # If we have enough audio (~1.2s), try to transcribe
                if len(audio_buffer) >= 6: 
                    full_audio = np.concatenate(audio_buffer)
                    
                    # Log that we are attempting transcription
                    if len(audio_buffer) % 10 == 0:
                        print(f"\n🎙️  Checking for speech in {len(full_audio)/16000:.1f}s of audio...", end=' ', flush=True)
                    
                    text = stt.transcribe(full_audio)
                    print("done")
                    
                    if text and len(text.strip()) > 3:
                        print(f"📝 You: {text}")
                        # Send transcription back to UI
                        await websocket.send_json({"type": "transcription", "text": text})
                        
                        # Stop listening until bot finishes responding and speaking
                        is_listening = False
                        
                        # Clear buffer immediately to prevent stale audio from affecting next turn
                        audio_buffer = []
                        
                        # Get LLM response and buffer it
                        print("🤔 Thinking...", end=' ', flush=True)
                        full_response = ""
                        for sentence in llm.stream_sentences(text):
                            if sentence and sentence.strip():
                                print(".", end='', flush=True)
                                full_response += sentence + " "
                                # Still send text to UI in real-time
                                await websocket.send_json({"type": "text", "text": sentence + " "})
                        
                        print(f"\n🤖 Bot: {full_response.strip()}")
                        
                        # Generate TTS for the WHOLE response at once
                        if full_response.strip():
                            print(f"🔊 Generating full speech response...")
                            try:
                                tts_obj = gTTS(text=full_response.strip(), lang='en')
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
                        
                        print(f"\n🤖 Bot: {full_response.strip()}")
                        print(f"🔊 Speaking response...\n")
                        
                        audio_buffer = [] # Redundant but safe
                    elif len(audio_buffer) > 100: # Max 6 seconds of no transcription
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
    print("🌍 SERVER STARTING AT: http://localhost:8001")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)
