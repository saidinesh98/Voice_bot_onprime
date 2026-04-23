# llm_client.py - Multi-lingual version
import requests
import json
import time
import re

class LLMClient:
    """Multi-lingual LLM Client - Centralized version"""
    
    def __init__(self, server_url="http://172.20.100.68:8000"):
        self.server_url = server_url.rstrip('/')
        self.session_id = f"session_{int(time.time())}"
        self.conversation_history = {} 

    def clear_history(self):
        """Clear session-side history"""
        self.conversation_history = {}
        try:
            requests.post(f"{self.server_url}/clear", json={"session_id": self.session_id})
        except:
            pass

    def stream_sentences(self, user_text, language='en'):
        """Stream from the centralized server"""
        try:
            # Simple state tracking to help with local logic if needed
            if language not in self.conversation_history:
                self.conversation_history[language] = True

            payload = {
                "text": user_text,
                "session_id": f"{self.session_id}_{language}",
                "language": language
            }
            
            # Send to server (server.py handles the persona and prompts)
            response = requests.post(
                f"{self.server_url}/chat/stream",
                json=payload,
                stream=True,
                timeout=30
            )

            if response.status_code != 200:
                yield f"Error: LLM server returned {response.status_code}"
                return

            buffer = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        try:
                            data = json.loads(decoded_line[6:])
                            if "token" in data:
                                token = data["token"]
                                buffer += token
                                
                                # Split into sentences (works for multiple languages)
                                # Split by punctuation but NOT by commas (to avoid choppy speech)
                                sentences = re.split(r'(?<=[.!?।॥])\s+', buffer)
                                
                                for sentence in sentences[:-1]:
                                    s = sentence.strip()
                                    if s:
                                        yield s
                                buffer = sentences[-1]
                            
                            if data.get("done"):
                                break
                        except:
                            continue
            
            if buffer.strip():
                yield buffer.strip()

        except Exception as e:
            print(f"LLM Client Error: {e}")
            yield f"I'm sorry, I encountered an error: {e}"

# Test
if __name__ == "__main__":
    llm = LLMClient()
    print("Testing interaction...")
    for sentence in llm.stream_sentences("Hello!", 'en'):
        print(f"Response: {sentence}")