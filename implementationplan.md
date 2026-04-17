###System setup and python environment

Update system & install audio libs
Install PortAudio (required by PyAudio/sounddevice) and build tools.
sudo apt update && sudo apt upgrade -y
sudo apt install -y portaudio19-dev python3-dev \
  python3-pip python3-venv ffmpeg git curl build-essential
Create isolated Python environment
Use a venv to keep all packages clean and reproducible.
python3 -m venv ~/voicebot
source ~/voicebot/bin/activate
pip install --upgrade pip wheel setuptools
Install all Python dependencies
pip install faster-whisper sounddevice numpy \
  silero-vad onnxruntime torch --index-url \
  https://download.pytorch.org/whl/cpu \
  piper-tts requests
faster-whisper silero-vad piper-tts sounddevice

###Install and configure Ollama(LLM)

Install Ollama
One-liner installer, sets up a systemd service automatically.
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
Pull a CPU-friendly model
For 16GB RAM: use mistral:7b-q4_K_M (~4.1GB) or llama3.2:3b (~2GB for faster response).
ollama pull mistral:7b-instruct-q4_K_M
# or faster, lighter option:
ollama pull llama3.2:3b
Tune Ollama for 32 cores
Set thread count and context size via env vars in the systemd override.
sudo systemctl edit ollama
# Add these lines:
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_NUM_THREAD=28"

Test the API
curl http://localhost:11434/api/generate -d '{
  "model": "mistral:7b-instruct-q4_K_M",
  "prompt": "Hello! Respond in one sentence.",
  "stream": false
}'

###Dowload stt and tts models

Download Faster-Whisper model
Use the small.en model for English-only (~480MB). Use small for multilingual.
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small.en', device='cpu', compute_type='int8')
print('STT model ready')
"
Download Piper TTS voice
Piper is the best CPU TTS — fast, lightweight C++ binary. Pick an English voice.
mkdir -p ~/voicebot/models/piper
cd ~/voicebot/models/piper

# Download a voice (en_US-lessac-medium is natural sounding)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/\
en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/\
en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
Test Piper TTS
echo "Hello, voice bot is working!" | \
  piper --model ~/voicebot/models/piper/en_US-lessac-medium.onnx \
  --output_file test.wav && aplay test.wav

###Build the pipeline modules

audio_capture.py — mic input with VAD
Continuously records in 30ms chunks; Silero VAD detects when speech starts/stops and returns a clean audio buffer.
import sounddevice as sd, numpy as np, torch

class AudioCapture:
    def __init__(self, rate=16000, chunk=480):
        self.rate = rate
        self.chunk = chunk
        model, utils = torch.hub.load(
            'snakers4/silero-vad', 'silero_vad', trust_repo=True)
        self.vad = model
        self.get_speech = utils[0]

    def record_utterance(self, silence_sec=1.2):
        frames, speaking = [], False
        silence_frames = int(self.rate * silence_sec / self.chunk)
        silent = 0
        with sd.InputStream(samplerate=self.rate, channels=1,
                            dtype='float32', blocksize=self.chunk) as s:
            while True:
                data, _ = s.read(self.chunk)
                chunk = data.squeeze()
                prob = self.vad(torch.from_numpy(chunk),
                                self.rate).item()
                if prob > 0.5:
                    speaking = True
                    silent = 0
                    frames.append(chunk)
                elif speaking:
                    frames.append(chunk)
                    silent += 1
                    if silent >= silence_frames:
                        break
        return np.concatenate(frames) if frames else None

stt.py — speech to text
from faster_whisper import WhisperModel

class STT:
    def __init__(self):
        self.model = WhisperModel(
            'small.en', device='cpu', compute_type='int8',
            cpu_threads=8, num_workers=2)

    def transcribe(self, audio_np):
        segs, _ = self.model.transcribe(
            audio_np, beam_size=3, language='en',
            vad_filter=True)
        return ' '.join(s.text.strip() for s in segs)

llm.py — streaming LLM via Ollama
Streams response sentence by sentence so TTS can start while LLM is still generating.
import requests, json, re

SYSTEM = "You are a helpful voice assistant. Reply concisely in 1-3 sentences."

class LLM:
    def __init__(self, model='mistral:7b-instruct-q4_K_M'):
        self.model = model
        self.history = [{'role':'system','content':SYSTEM}]

    def stream_sentences(self, user_text):
        self.history.append({'role':'user','content':user_text})
        resp = requests.post('http://localhost:11434/api/chat',
            json={'model':self.model,'messages':self.history,
                  'stream':True}, stream=True)
        buf, full = '', ''
        for line in resp.iter_lines():
            if not line: continue
            chunk = json.loads(line).get('message',{}).get('content','')
            buf += chunk; full += chunk
            for sent in re.split(r'(?<=[.!?])\s+', buf):
                if re.search(r'[.!?]$', sent):
                    yield sent.strip()
                    buf = buf[buf.index(sent)+len(sent):].lstrip()
        if buf.strip(): yield buf.strip()

###wire it together--main.py

main.py — the full loop
Sentence-by-sentence streaming: LLM generates → TTS speaks each sentence → LLM continues. Minimizes time to first audio.
from audio_capture import AudioCapture
from stt import STT
from llm import LLM
from tts import TTS

def main():
    print("Loading models...")
    mic   = AudioCapture()
    stt   = STT()
    llm   = LLM()
    tts   = TTS()
    print("Voice bot ready! Press Ctrl+C to quit.\n")

    while True:
        print("Listening...")
        audio = mic.record_utterance()
        if audio is None:
            continue

        print("Transcribing...")
        text = stt.transcribe(audio)
        if not text.strip():
            continue
        print(f"You: {text}")

        print("Bot: ", end='', flush=True)
        for sentence in llm.stream_sentences(text):
            print(sentence, end=' ', flush=True)
            tts.speak(sentence)
        print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")


>test,optimise and run as a service
Benchmark each stage
Time each component to find your bottleneck before optimizing.
import time
# Wrap each call: start = time.perf_counter()
# print(f"STT: {time.perf_counter()-start:.2f}s")
CPU threading tweaks
Leave 4 cores for OS. Spread threads: 8 for Whisper, 20+ for Ollama (set via env), 4 idle.
export OMP_NUM_THREADS=8        # Whisper / numpy
export OLLAMA_NUM_THREAD=20     # Ollama LLM inference
Run as a systemd service (optional)
sudo nano /etc/systemd/system/voicebot.service
# [Unit] Description=Local Voice Bot
# [Service] ExecStart=/home/user/voicebot/bin/python main.py
#           WorkingDirectory=/home/user/voicebot
# [Install] WantedBy=multi-user.target
sudo systemctl enable voicebot --now
