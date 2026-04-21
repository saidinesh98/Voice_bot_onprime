import os
from datetime import datetime
import json
import asyncio
import base64
import numpy as np
import io
import re
import time
from functools import partial
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import torch
from multi_lingual.stt import STT
from multi_lingual.llm_client import LLMClient
from multi_lingual.tts_local import TTSLocal
from database_manager import DatabaseManager
from auth_utils import verify_token
from langdetect import detect, DetectorFactory
# Ensure consistent results for langdetect
DetectorFactory.seed = 0

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("\n📦 Loading Multi-lingual Models...")
stt = STT(model_size='tiny') # Changed to tiny for speed
tts_local = TTSLocal()
llm_url = os.getenv("LLM_SERVER_URL", "http://llm-server:8000")
llm = LLMClient(server_url=llm_url)
db = DatabaseManager()

# Wait a few seconds for the DB to be ready before initializing
print("⏳ Waiting for database to stabilize...")
time.sleep(5)
db.initialize_database()

# Load Silero VAD
print("🎙️  Loading Silero VAD...")
vad_model, vad_utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', trust_repo=True)
(get_speech_timestamps, save_audio, read_audio, VADIteratorCollector, collect_chunks) = vad_utils


LANG_MAP = {
    'hi': 'hi', 'ta': 'ta', 'te': 'te', 'ml': 'ml', 'bn': 'bn',
    'ar': 'ar', 'en': 'en', 'fr': 'fr', 'de': 'de', 'es': 'es', 'ko': 'ko', 'pl': 'pl'
}

# Removed _tts_sync as we now use TTSLocal through run_pipeline


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user_payload = verify_token(token)

    if not user_payload:
        print("❌ Unauthorized: Missing or invalid Keycloak token")
        await websocket.accept()
        await websocket.close(code=4001)
        return

    await websocket.accept()
    user_name = user_payload.get("preferred_username", "Unknown User")
    print(f"\n{'='*60}\n🚀  FRONTEND CONNECTED (User: {user_name})\n{'='*60}")

    # Heartbeat task to keep Cloudflare/Gateways alive
    async def send_heartbeat():
        try:
            while True:
                await asyncio.sleep(10)
                if websocket.client_state.value == 1: # Open
                    await websocket.send_json({"type": "ping"})
        except:
            pass
    
    heartbeat_task = asyncio.create_task(send_heartbeat())

    loop = asyncio.get_event_loop()
    audio_buffer = []
    # transcribing: STT running in background — keep buffering audio but don't start another STT
    # processing:   valid speech found, LLM/TTS running — discard incoming audio
    transcribing = False
    processing = False
    # Once the first language is detected reliably, we lock it for the session
    session_state = {"locked_lang": None}
    was_speaking = False
    silence_duration = 0  # In chunks
    
    # Track when the last pipeline was triggered to avoid overlap
    last_trigger_time = 0

    async def run_pipeline(audio_snapshot):
        nonlocal transcribing, processing
        try:
            # STT in thread — event loop stays free to receive audio chunks
            text, detected_lang = await loop.run_in_executor(
                None, lambda: stt.transcribe(audio_snapshot, detect_language=True)
            )

            if not text or len(text.strip()) <= 3:
                print(f"⏳ No clear speech detected (buffer: {len(audio_buffer)} new chunks)")
                return

            # --- TEXT-BASED LANGUAGE CORRECTION ---
            try:
                # Protection for short common English words
                if text.lower().strip() in ["yes", "no", "ok", "hello", "hi"]:
                    text_lang = "en"
                else:
                    text_lang = detect(text)
                
                if text_lang != detected_lang:
                    # Special check for Chinese (langdetect uses 'zh-cn' or 'zh-tw', we use 'zh')
                    corr_lang = text_lang.split('-')[0]
                    if corr_lang != detected_lang:
                        print(f"🔄 Correcting language from {detected_lang} to {corr_lang} based on text")
                        detected_lang = corr_lang
            except Exception as e:
                # langdetect fails if no features, just keep whisper's guess
                pass
            # --------------------------------------

            # Valid speech — lock out new audio until response is done
            processing = True
            audio_buffer.clear()

            # --- LANGUAGE LOCKING ---
            if session_state["locked_lang"]:
                detected_lang = session_state["locked_lang"]
            else:
                session_state["locked_lang"] = detected_lang
                print(f"🔒 Language locked to: {detected_lang.upper()}")
            # ------------------------

            print(f"\n📝 You [{detected_lang.upper()}]: {text}")
            try:
                await websocket.send_json({"type": "transcription", "text": text, "language": detected_lang})
            except Exception:
                print("⚠️  Failed to send transcription (client disconnected)")
                return

            # Lead capture
            clean_text = text.replace(" ", "")
            phone_match = re.search(r'\d{10,12}', clean_text)
            name = None
            name_match = re.search(r"(?:my name is|i am|this is)\s+([a-zA-Z]+)", text.lower())
            if name_match:
                name = name_match.group(1).capitalize()
            if phone_match or name:
                phone = phone_match.group() if phone_match else None
                interest = next(
                    (p for p in ["SAMANA Hills", "SAMANA Palm Vista", "SAMANA Creek Horizon"]
                     if p.lower() in text.lower()), None
                )
                db.add_lead(phone=phone, name=name, project=interest, raw_text=text)
                print(f"📍 Lead: {name or 'User'} ({phone or 'No phone'}) — {interest or 'General'}")

            # LLM streaming in background thread via queue — event loop stays free
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤔 LLM Request started for {detected_lang}...", flush=True)
            
            # Ensure we have a valid key for LANG_MAP
            lang_key = str(detected_lang).lower()[:2]
            gtts_lang = LANG_MAP.get(lang_key, 'en')
            
            sentence_queue: asyncio.Queue = asyncio.Queue()

            def _stream_llm():
                try:
                    for s in llm.stream_sentences(text, detected_lang):
                        asyncio.run_coroutine_threadsafe(sentence_queue.put(s), loop)
                except Exception as e:
                    print(f"\n❌ LLM stream error: {e}")
                finally:
                    asyncio.run_coroutine_threadsafe(sentence_queue.put(None), loop)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 LLM Stream thread launched", flush=True)
            loop.run_in_executor(None, _stream_llm)

            full_response = ""
            pending_tts = None
            prev_sentence = None

            while True:
                sentence = await sentence_queue.get()
                
                # If we have a previous sentence and its audio is ready, send them together
                if pending_tts is not None:
                    try:
                        audio_wav = await pending_tts
                        if audio_wav:
                            # Deliver Sentence N-1
                            try:
                                await websocket.send_json({"type": "text", "text": prev_sentence + " "})
                                await websocket.send_bytes(audio_wav)
                            except Exception:
                                print("⚠️ Failed to send data (client disconnected)")
                                return
                    except Exception as tts_err:
                        print(f"⚠️ TTS Error: {tts_err}")

                if sentence is None:
                    break
                if not sentence.strip():
                    continue

                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🗯️ Received sentence: '{sentence[:50]}...'", flush=True)
                
                # Full response for logs
                full_response += sentence + " "
                prev_sentence = sentence

                # Start TTS for CURRENT sentence
                pending_tts = loop.run_in_executor(None, partial(tts_local.generate_wav, sentence, detected_lang))

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🤖 Bot [{detected_lang.upper()}]: {full_response.strip()}")
            print("✅ Full response sent\n")

        except Exception as e:
            print(f"\n❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            transcribing = False
            processing = False

    try:
        while True:
            try:
                message = await websocket.receive()
            except Exception:
                break

            if message.get("type") == "websocket.disconnect":
                break

            if "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "config":
                    print(f"⚙️  Config: {data}")
                elif data.get("type") == "resume_listening":
                    print("\n🔄 Bot finished speaking. Resuming listening...")
                    audio_buffer.clear()
                continue

            if "bytes" in message:
                if processing:
                    continue  # bot is responding — discard audio

                audio_chunk = np.frombuffer(message["bytes"], dtype=np.int16).astype(np.float32) / 32768.0
                audio_buffer.append(audio_chunk)

                # VAD Check on every chunk
                # Silero VAD requires chunks of exactly 512 samples at 16000Hz
                # Frontend sends 4096 samples. We split this into 512-sample windows.
                try:
                    speech_prob = 0
                    for i in range(0, len(audio_chunk), 512):
                        window = audio_chunk[i:i+512]
                        if len(window) < 512:
                            continue
                        prob = vad_model(torch.from_numpy(window), 16000).item()
                        speech_prob = max(speech_prob, prob)
                except Exception as e:
                    print(f"VAD Error: {e}")
                    speech_prob = 0

                if speech_prob > 0.4:  # Slightly lower threshold for sub-chunks
                    if not was_speaking:
                        print(f"🗣️  Speech started... (prob: {speech_prob:.3f})")
                    was_speaking = True
                    silence_duration = 0
                else:
                    if was_speaking:
                        silence_duration += 1
                        # 4096 samples at 16kHz is 256ms. 
                        # 2 chunks = 512ms silence.
                        if silence_duration >= 2:
                            print(f"🤫  Silence detected ({silence_duration} chunks). Triggering STT...")
                            was_speaking = False
                            silence_duration = 0

                            
                            if not transcribing:
                                transcribing = True
                                snapshot = np.concatenate(audio_buffer)
                                audio_buffer = []
                                asyncio.create_task(run_pipeline(snapshot))

                if len(audio_buffer) > 100:
                    # Slide window if no speech detected for a long time
                    audio_buffer = audio_buffer[20:]

    except WebSocketDisconnect:
        print("\n🔌 Frontend disconnected cleanly")
    except Exception as e:
        print(f"\n❌ WebSocket error: {e}")
    finally:
        heartbeat_task.cancel()
        print("🛑 Session ended\n")


frontend_dist = os.path.join("frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🌍 MULTI-LINGUAL SERVER STARTING AT: http://localhost:8001")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)
