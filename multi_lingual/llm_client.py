# llm_client.py - Multi-lingual version
import requests
import json
import re

class LLMClient:
    """Multi-lingual LLM Client"""
    
    # Language prompts for system message
    LANGUAGE_PROMPTS = {
        'en': "You are a helpful assistant. Respond in English.",
        'hi': "आप एक सहायक हैं। हिंदी में जवाब दें।",
        'ta': "நீங்கள் ஒரு உதவியாளர். தமிழில் பதிலளிக்கவும்.",
        'te': "మీరు సహాయకుడు. తెలుగులో సమాధానం ఇవ్వండి.",
        'ml': "നിങ്ങൾ ഒരു സഹായിയാണ്. മലയാളത്തിൽ മറുപടി നൽകുക.",
        'bn': "আপনি একজন সাহায্যকারী। বাংলায় উত্তর দিন।",
        'fr': "Vous êtes un assistant. Répondez en français.",
        'de': "Sie sind ein Assistent. Antworten Sie auf Deutsch.",
        'es': "Eres un asistente. Responde en español.",
        'zh': "你是一个助手。用中文回答。",
        'ja': "あなたはアシスタントです。日本語で答えてください。",
        'kn': "ನೀವು ಒಬ್ಬ ಸಹಾಯಕ. ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ.",
        'mr': "तुम्ही एक मदतनीस आहात. मराठीत उत्तर द्या.",
        'gu': "તમે એક મદદગાર છો. ગુજરાતીમાં જવાબ આપો.",
        'pa': "ਤੁਸੀਂ ਇੱਕ ਸਹਾਇਕ ਹੋ। ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ।",
        'ur': "آپ ایک مددگار ہیں۔ اردو میں جواب دیں۔",
        'ru': "Вы помощник. Отвечайте на русском."
    }
    
    def __init__(self, server_url="http://172.20.100.68:8000"):
        self.server_url = server_url.rstrip('/')
        self.session_id = "windows_client"
        self.current_language = 'en'
        self.conversation_history = {}  # Separate history per language
        print(f"✅ Connected to LLM server at {self.server_url}")
    
    def stream_sentences(self, user_text, language='en'):
        """Stream response in specified language"""
        self.current_language = language
        
        # Get language-specific system prompt
        system_prompt = self.LANGUAGE_PROMPTS.get(language, 
                         f"You are a helpful assistant. Respond in {language}.")
        
        # Initialize history for this language if not exists
        if language not in self.conversation_history:
            self.conversation_history[language] = [
                {"role": "system", "content": system_prompt}
            ]
        
        # Add user message
        self.conversation_history[language].append(
            {"role": "user", "content": user_text}
        )
        
        try:
            response = requests.post(
                f"{self.server_url}/chat/stream",
                json={
                    "text": user_text,
                    "session_id": f"{self.session_id}_{language}",
                    "language": language,
                    "system_prompt": system_prompt
                },
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                yield f"Server error: {response.status_code}"
                return
            
            buffer = ""
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                        if line_str.startswith('data: '):
                            line_str = line_str[6:]
                        
                        data = json.loads(line_str)
                        
                        if 'token' in data:
                            token = data['token']
                            buffer += token
                            full_response += token
                            
                            # Split into sentences (works for multiple languages)
                            # Split by punctuation but ALSO by max length and special markers
                            # This ensures we don't wait for a 50-word sentence to finish
                            sentences = re.split(r'(?<=[.!?।॥,])\s+', buffer)
                            
                            for sentence in sentences[:-1]:
                                s = sentence.strip()
                                # Allow much longer sentences (up to 150 chars) for smoother speech
                                while len(s) > 150:
                                    # Try to find a space or comma near 130 characters
                                    cut_idx = s.rfind(' ', 0, 150)
                                    if cut_idx == -1: cut_idx = s.rfind(',', 0, 150)
                                    if cut_idx == -1: cut_idx = 130 # Fallback
                                    
                                    chunk = s[:cut_idx].strip()
                                    if chunk: yield chunk
                                    s = s[cut_idx:].strip()
                                
                                if s: yield s
                            buffer = sentences[-1] if sentences else ""
                    except:
                        continue
            
            if buffer.strip():
                yield buffer.strip()
            
            # Save to history
            if full_response:
                self.conversation_history[language].append(
                    {"role": "assistant", "content": full_response}
                )
                
                # Keep history manageable
                if len(self.conversation_history[language]) > 21:
                    self.conversation_history[language] = [
                        self.conversation_history[language][0]
                    ] + self.conversation_history[language][-20:]
                    
        except Exception as e:
            yield f"Error: {e}"
    
    def clear_history(self, language=None):
        """Clear conversation history"""
        if language:
            self.conversation_history[language] = []
        else:
            self.conversation_history = {}

# Test
if __name__ == "__main__":
    llm = LLMClient()
    print("Testing Hindi...")
    for sentence in llm.stream_sentences("Namaste, aap kaise hain?", 'hi'):
        print(f"Hindi: {sentence}")