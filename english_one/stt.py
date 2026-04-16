#!/usr/bin/env python3
"""
STT for Windows - Uses faster-whisper
"""
from faster_whisper import WhisperModel
import numpy as np

class STT:
    """Local Speech-to-Text using Faster-Whisper"""
    
    def __init__(self, model_size='small.en'):
        print(f"Loading STT model ({model_size})...")
        # Windows optimized settings
        self.model = WhisperModel(
            model_size,
            device='cpu',
            compute_type='int8',  # Use int8 for faster CPU inference
            cpu_threads=4,
            num_workers=2
        )
        print("✅ STT ready")
    
    def transcribe(self, audio_np):
        """Convert audio to text"""
        if audio_np is None or len(audio_np) < 8000:  # Less than 0.5 seconds
            return ""
        
        # Ensure audio is float32
        if audio_np.dtype != np.float32:
            audio_np = audio_np.astype(np.float32)
        
        # Transcribe
        segments, info = self.model.transcribe(
            audio_np,
            beam_size=3,
            language='en',
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                threshold=0.5
            )
        )
        
        # Combine all segments
        text = ' '.join(segment.text.strip() for segment in segments)
        
        return text.strip()
    
    def transcribe_file(self, audio_file):
        """Transcribe from WAV file"""
        import wave
        import struct
        
        with wave.open(audio_file, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        
        return self.transcribe(audio)