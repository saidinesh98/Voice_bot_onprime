#!/usr/bin/env python3
"""
LLM Client for VM Server - Fixed version with better error handling
"""
import requests
import json
import re
import time

class LLMClient:
    """Client for VM LLM Server"""
    
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url.rstrip('/')
        self.session_id = "windows_client"
        print(f"✅ Connected to LLM server at {self.server_url}")
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test if server is reachable"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=3)
            if response.status_code == 200:
                print("✅ Server health check passed")
                return True
        except Exception as e:
            print(f"⚠️  Server connection test failed: {e}")
        return False
    
    def stream_sentences(self, user_text):
        """Stream response sentence by sentence - Fixed"""
        print(f"🔄 Sending to server: {user_text[:50]}...")
        
        try:
            response = requests.post(
                f"{self.server_url}/chat/stream",
                json={
                    "text": user_text,
                    "session_id": self.session_id
                },
                stream=True,
                timeout=60  # Increased timeout
            )
            
            print(f"📡 Server response status: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"Server error: {response.status_code}"
                print(f"❌ {error_msg}")
                yield error_msg
                return
            
            buffer = ""
            token_count = 0
            
            for line in response.iter_lines():
                if line:
                    try:
                        # Check if line starts with 'data: '
                        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                        if line_str.startswith('data: '):
                            line_str = line_str[6:]
                        
                        data = json.loads(line_str)
                        
                        if 'token' in data:
                            token = data['token']
                            token_count += 1
                            buffer += token
                            
                            # Split into sentences
                            sentences = re.split(r'(?<=[.!?])\s+', buffer)
                            for i, sentence in enumerate(sentences[:-1]):
                                if sentence.strip():
                                    print(f"📤 Yielding sentence: {sentence[:30]}...")
                                    yield sentence.strip()
                            buffer = sentences[-1] if sentences else ""
                        
                        elif 'error' in data:
                            print(f"❌ Server error: {data['error']}")
                            yield f"Server error: {data['error']}"
                            return
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON decode error: {e}")
                        continue
                    except Exception as e:
                        print(f"⚠️  Line processing error: {e}")
                        continue
            
            # Yield remaining buffer
            if buffer.strip():
                print(f"📤 Yielding remaining: {buffer[:30]}...")
                yield buffer.strip()
            
            print(f"✅ Stream complete. Tokens received: {token_count}")
            
            if token_count == 0:
                yield "I received your message but couldn't generate a response. Please try again."
                
        except requests.exceptions.Timeout:
            error_msg = "Request timed out. The server might be busy."
            print(f"❌ {error_msg}")
            yield error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to VM server. Is it running?"
            print(f"❌ {error_msg}")
            yield error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"❌ {error_msg}")
            yield error_msg
    
    def chat(self, text):
        """Non-streaming chat - for testing"""
        try:
            response = requests.post(
                f"{self.server_url}/chat",
                json={"text": text, "session_id": self.session_id},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Server error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def clear_history(self):
        """Clear conversation history on server"""
        try:
            response = requests.post(
                f"{self.server_url}/clear",
                json={"session_id": self.session_id},
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Conversation history cleared")
            else:
                print(f"⚠️  Clear history failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Clear history error: {e}")