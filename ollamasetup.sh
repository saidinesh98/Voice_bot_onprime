#!/bin/bash
# step2_ollama_setup.sh

echo "🤖 Phase 2: Ollama LLM Setup"

# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# 3. Wait for Ollama to initialize
sleep 5

# 4. Pull CPU-optimized model (choose one)
# Option A: Mistral 7B - better quality (~4.1GB)
ollama pull mistral:7b-instruct-q4_K_M

# 5. Optimize Ollama for your 32-core system
sudo mkdir -p /etc/systemd/system/ollama.service.d

sudo tee /etc/systemd/system/ollama.service.d/override.conf << EOF
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_NUM_THREAD=28"
Environment="OLLAMA_FLASH_ATTENTION=1"
EOF

# 6. Reload and restart Ollama with new config
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 7. Test Ollama API
sleep 3
curl http://localhost:11434/api/generate -d '{
  "model": "mistral:7b-instruct-q4_K_M",
  "prompt": "Hello! Respond in one sentence.",
  "stream": false
}'

echo "✅ Phase 2 Complete!"