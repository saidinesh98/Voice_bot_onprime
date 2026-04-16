#!/usr/bin/env python3
"""
Audio Capture for Windows - Uses Silero VAD instead of webrtcvad
"""
import sounddevice as sd
import numpy as np
import torch
import time

class AudioCapture:
    """Microphone capture with Silero VAD for Windows"""
    
    def __init__(self, rate=16000, chunk=512):
        self.rate = rate
        self.chunk = chunk
        
        # Load Silero VAD
        print("Loading VAD model...")
        try:
            model, utils = torch.hub.load(
                'snakers4/silero-vad',
                'silero_vad',
                trust_repo=True,
                verbose=False,
                force_reload=False
            )
            self.vad = model
            self.get_speech_timestamps = utils[0]
            print("✅ Silero VAD loaded")
        except Exception as e:
            print(f"⚠️  VAD loading failed: {e}")
            print("Using simple energy-based detection")
            self.vad = None
    
    def record_utterance(self, silence_sec=1.0, max_duration=10):
        """Record until silence detected"""
        frames = []
        speaking = False
        silent_chunks = 0
        silence_threshold = int(self.rate * silence_sec / self.chunk)
        max_chunks = int(self.rate * max_duration / self.chunk)
        
        print("🎤 Listening...", end=' ', flush=True)
        
        with sd.InputStream(
            samplerate=self.rate,
            channels=1,
            dtype='float32',
            blocksize=self.chunk
        ) as stream:
            
            while len(frames) < max_chunks:
                data, overflowed = stream.read(self.chunk)
                chunk = data.squeeze()
                
                # Detect speech
                if self.vad:
                    # Use Silero VAD
                    speech_prob = self.vad(torch.from_numpy(chunk), self.rate).item()
                    is_speech = speech_prob > 0.5
                else:
                    # Use energy-based detection (simpler)
                    energy = np.sqrt(np.mean(chunk**2))
                    is_speech = energy > 0.01
                
                if is_speech:
                    if not speaking:
                        print("🎙️ Speaking...", end=' ', flush=True)
                        speaking = True
                    silent_chunks = 0
                    frames.append(chunk)
                elif speaking:
                    frames.append(chunk)
                    silent_chunks += 1
                    if silent_chunks >= silence_threshold:
                        break
        
        if frames:
            audio = np.concatenate(frames)
            duration = len(audio) / self.rate
            print(f"Done ({duration:.1f}s)")
            
            # Normalize audio
            if np.abs(audio).max() > 0:
                audio = audio / np.abs(audio).max()
            
            return audio
        else:
            print("No speech detected")
            return None
    
    def test_microphone(self):
        """Test if microphone is working"""
        print("\n🎤 Testing microphone...")
        duration = 2
        print(f"Recording {duration} seconds...")
        
        recording = sd.rec(int(duration * self.rate), 
                          samplerate=self.rate, 
                          channels=1, 
                          dtype='float32')
        sd.wait()
        
        energy = np.sqrt(np.mean(recording**2))
        print(f"Audio energy level: {energy:.4f}")
        
        if energy > 0.005:
            print("✅ Microphone is working!")
            return True
        else:
            print("❌ Microphone seems silent. Check your input device.")
            return False