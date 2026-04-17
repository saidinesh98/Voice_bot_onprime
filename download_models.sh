#!/bin/bash
# step3_download_models.sh

echo "📥 Phase 3: Downloading AI Models"

cd ~/voicebot
source ~/voicebot/bin/activate

# 1. Download Faster-Whisper STT model (English-only, 480MB)
python3 -c "
from faster_whisper import WhisperModel
print('Downloading STT model (small.en)...')
model = WhisperModel('small.en', device='cpu', compute_type='int8')
print('✅ STT model ready')
"

# 2. Create Piper TTS models directory
mkdir -p ~/voicebot/models/piper
cd ~/voicebot/models/piper

# 3. Download natural English voice (lessac-medium)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Alternative faster voice (lessac-light)
# wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/light/en_US-lessac-light.onnx

# 4. Test Piper TTS
echo "Testing Piper TTS..." | piper --model ~/voicebot/models/piper/en_US-lessac-medium.onnx --output_file /tmp/test.wav
aplay /tmp/test.wav 2>/dev/null || echo "Audio test complete (aplay not available)"

echo "✅ Phase 3 Complete!"