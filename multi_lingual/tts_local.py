import os
import torch
import numpy as np
import io
import wave
from transformers import VitsModel, AutoTokenizer
from melo.api import TTS as MeloTTS

class TTSLocal:
    """
    Local Multi-lingual TTS using MeloTTS and Facebook MMS.
    Routes to the best model based on language.
    """
    
    def __init__(self, device='cpu'):
        # Optimize torch for CPU
        # Optimize torch for 32-core environment
        torch.set_num_threads(16)
        self.device = device
        self.melo_models = {}  # Cache for MeloTTS models
        self.mms_models = {}   # Cache for MMS models
        self.mms_tokenizers = {}
        
        # Languages supported by MeloTTS
        self.MELO_LANGS = {
            'en': 'EN'
        }
        
        # Languages supported by MMS (HuggingFace model paths)
        self.MMS_LANGS = {
            'hi': 'facebook/mms-tts-hin',
            'ta': 'facebook/mms-tts-tam',
            'te': 'facebook/mms-tts-tel',
            'ar': 'facebook/mms-tts-ara',
            'de': 'facebook/mms-tts-deu',
        }
        
        print(f"✅ TTSLocal initialized on {device}")
        # Warmup English model immediately
        try:
            print("🔥 Warming up TTS engines (pre-loading BERT and VITS models)...", flush=True)
            # Perform a tiny dummy synthesis to force-load BERT into RAM
            self.generate_wav("Warmup", lang='en')
            print("✅ TTS engines fully warmed up and cached in RAM!")
        except Exception as e:
            print(f"⚠️ TTS Warmup failed: {e}")

    def _get_melo_model(self, lang_code):
        if lang_code not in self.melo_models:
            print(f"📦 Downloading/Loading MeloTTS model for {lang_code}... (this may take a minute on first run)", flush=True)
            self.melo_models[lang_code] = MeloTTS(language=lang_code, device=self.device)
            print(f"✅ MeloTTS model for {lang_code} loaded!", flush=True)
        return self.melo_models[lang_code]

    def _get_mms_model(self, lang_code):
        model_path = self.MMS_LANGS.get(lang_code)
        if lang_code not in self.mms_models:
            print(f"📦 Downloading/Loading MMS model for {lang_code} ({model_path})...", flush=True)
            self.mms_tokenizers[lang_code] = AutoTokenizer.from_pretrained(model_path)
            self.mms_models[lang_code] = VitsModel.from_pretrained(model_path).to(self.device)
            print(f"✅ MMS model for {lang_code} loaded!", flush=True)
        return self.mms_models[lang_code], self.mms_tokenizers[lang_code]

    def generate_wav(self, text, lang='en'):
        """Generates WAV bytes for the given text and language."""
        lang = lang.lower()
        
        try:
            if lang in self.MELO_LANGS:
                melo_lang = self.MELO_LANGS[lang]
                model = self._get_melo_model(melo_lang)
                speaker_ids = model.hps.data.spk2id
                # Use default speaker for the language
                accent = f"{melo_lang}-Default" if f"{melo_lang}-Default" in speaker_ids else list(speaker_ids.keys())[0]
                
                # In most VITS implementations, it's model.model.infer or similar.
                # MeloTTS API usually has tts_to_file. I'll use a BytesIO.
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                
                model.tts_to_file(text, speaker_ids[accent], tmp_path, speed=1.0)
                
                with open(tmp_path, "rb") as f:
                    wav_bytes = f.read()
                
                os.unlink(tmp_path)
                return wav_bytes

            elif lang in self.MMS_LANGS:
                model, tokenizer = self._get_mms_model(lang)
                inputs = tokenizer(text, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    output = model(**inputs).waveform.cpu().numpy()
                
                # Convert to WAV bytes
                return self._numpy_to_wav(output[0], model.config.sampling_rate)

            else:
                # Fallback to English MeloTTS
                print(f"⚠️ Language {lang} not supported, falling back to English")
                return self.generate_wav(text, lang='en')

        except Exception as e:
            print(f"❌ TTS Generation Error ({lang}): {e}")
            import traceback
            traceback.print_exc()
            return None

    def _numpy_to_wav(self, audio_np, sample_rate):
        """Converts numpy array to WAV bytes."""
        # Normalize to int16
        audio_int16 = (audio_np * 32767).astype(np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes for int16
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return buffer.getvalue()

if __name__ == "__main__":
    # Quick test
    tts = TTSLocal()
    wav = tts.generate_wav("Hello, this is a local test of the voice bot.", lang='en')
    if wav:
        with open("test_en.wav", "wb") as f:
            f.write(wav)
        print("✅ Saved test_en.wav")
