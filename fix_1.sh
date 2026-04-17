# 1. Create the models directory in your current path
mkdir -p "/home/administrator/Voice bot/onprime/models/piper"

# 2. Copy the model files to your working directory
cp /home/administrator/voicebot/models/piper/en_US-lessac-medium.onnx \
   "/home/administrator/Voice bot/onprime/models/piper/"

cp /home/administrator/voicebot/models/piper/en_US-lessac-medium.onnx.json \
   "/home/administrator/Voice bot/onprime/models/piper/" 2>/dev/null

# 3. Copy piper binaries
cp -r /home/administrator/voicebot/onprime/piper \
   "/home/administrator/Voice bot/onprime/" 2>/dev/null

# 4. Verify the files are now there
ls -la "/home/administrator/Voice bot/onprime/models/piper/"