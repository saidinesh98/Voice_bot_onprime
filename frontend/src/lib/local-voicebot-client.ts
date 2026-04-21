export type LocalConfig = {
  voiceName?: string;
  audioContext?: AudioContext;
  token?: string;
};

export class LocalVoiceBotClient {
  private ws: WebSocket | null = null;
  private audioContext: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private isConnected = false;
  private isRecordingEnabled = true;

  constructor() {}

  async connect(config: LocalConfig, callbacks: {
    onMessage?: (text: string) => void;
    onAudio?: (data: Float32Array) => void;
    onInterrupted?: () => void;
    onError?: (err: any) => void;
    onClose?: () => void;
    onTranscription?: (text: string) => void;
  }) {
    this.audioContext = config.audioContext || null;
    
    return new Promise<void>((resolve, reject) => {
      const host = window.location.host;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = config.token 
        ? `${protocol}//${host}/ws?token=${config.token}`
        : `${protocol}//${host}/ws`;
      this.ws = new WebSocket(url);
      
      this.ws.onopen = () => {
        this.isConnected = true;
        console.log("Connected to Local Voice Bot Backend");
        const { audioContext, ...filteredConfig } = config;
        this.ws?.send(JSON.stringify({ type: "config", ...filteredConfig }));
        resolve();
      };

      this.ws.onmessage = async (event) => {
        try {
          if (event.data instanceof Blob) {
            // Binary audio message (WAV from MeloTTS/MMS)
            if (callbacks.onAudio) {
              const arrayBuffer = await event.data.arrayBuffer();
              const audioBuffer = await this.audioContext?.decodeAudioData(arrayBuffer);
              if (audioBuffer) {
                callbacks.onAudio(audioBuffer.getChannelData(0));
              }
            }
            return;
          }

          const data = JSON.parse(event.data);
          
          if (data.type === 'text' && callbacks.onMessage) {
            callbacks.onMessage(data.text);
          }
          
          if (data.type === 'transcription' && callbacks.onTranscription) {
            callbacks.onTranscription(data.text);
          }

          if (data.type === 'audio' && callbacks.onAudio) {
            // Fallback for legacy base64 audio
            const binaryString = atob(data.data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            
            const audioBuffer = await this.audioContext?.decodeAudioData(bytes.buffer);
            if (audioBuffer) {
                callbacks.onAudio(audioBuffer.getChannelData(0));
            }
          }
        } catch (e) {
          console.error("Error processing message:", e);
        }
      };
      // ... (rest of connect)

      this.ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        if (callbacks.onError) callbacks.onError(err);
        reject(err);
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        if (callbacks.onClose) callbacks.onClose();
      };
    });
  }

  async startMicrophone() {
    if (!this.isConnected || !this.ws) return;

    // Use a dedicated 16kHz context for recording to match STT requirements
    const recordingContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const source = recordingContext.createMediaStreamSource(this.stream);
    const processor = recordingContext.createScriptProcessor(4096, 1, 1);
    
    processor.onaudioprocess = (e) => {
      if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN || !this.isRecordingEnabled) return;
      const inputData = e.inputBuffer.getChannelData(0);
      const pcmData = this.float32ToInt16(inputData);
      this.ws.send(pcmData.buffer);
    };

    source.connect(processor);
    processor.connect(recordingContext.destination);
    
    // Save context to close it later
    (this as any).recordingContext = recordingContext;
  }

  stopMicrophone() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if ((this as any).recordingContext) {
      (this as any).recordingContext.close();
    }
  }

  setRecordingEnabled(enabled: boolean) {
    this.isRecordingEnabled = enabled;
    console.log(`🎤 Microphone ${enabled ? 'resumed' : 'paused'} sending audio`);
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    this.stopMicrophone();
    if (this.ws) {
      this.ws.close();
    }
    this.isConnected = false;
  }

  private float32ToInt16(buffer: Float32Array): Int16Array {
    const l = buffer.length;
    const buf = new Int16Array(l);
    for (let i = 0; i < l; i++) {
      buf[i] = Math.min(1, Math.max(-1, buffer[i])) * 0x7FFF;
    }
    return buf;
  }
}
