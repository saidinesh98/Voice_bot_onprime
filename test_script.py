# test_windows_bot.py - Complete test script
import sys
import time
import requests

def test_vm_connection():
    """Test VM server connection"""
    VM_IP = "172.20.100.68"
    VM_PORT = 8000
    
    print("="*60)
    print("Testing VM Server Connection")
    print("="*60)
    
    # Test health
    try:
        resp = requests.get(f"http://{VM_IP}:{VM_PORT}/health", timeout=5)
        print(f"✅ Health check: {resp.status_code}")
        print(f"   Response: {resp.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test chat
    print("\n📝 Testing chat endpoint...")
    try:
        resp = requests.post(
            f"http://{VM_IP}:{VM_PORT}/chat",
            json={"text": "Say hello in one word", "session_id": "test"},
            timeout=30
        )
        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ Chat response: {result.get('response', 'No response')}")
        else:
            print(f"❌ Chat failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False
    
    return True

def test_local_components():
    """Test local STT and TTS"""
    print("\n" + "="*60)
    print("Testing Local Components")
    print("="*60)
    
    # Test STT
    try:
        from stt import STT
        stt = STT()
        print("✅ STT loaded")
    except Exception as e:
        print(f"❌ STT error: {e}")
    
    # Test TTS
    try:
        from tts import TTS
        tts = TTS()
        print("✅ TTS loaded")
        tts.speak("Testing voice output")
    except Exception as e:
        print(f"❌ TTS error: {e}")

def test_llm_client():
    """Test LLM client"""
    print("\n" + "="*60)
    print("Testing LLM Client")
    print("="*60)
    
    from llm_client import LLMClient
    client = LLMClient(server_url="http://172.20.100.68:8000")
    
    print("\nSending test message...")
    response_text = ""
    for sentence in client.stream_sentences("Say 'Hello Windows bot' in 3 words"):
        print(f"Received: '{sentence}'")
        response_text += sentence
    
    if response_text:
        print(f"\n✅ Full response: {response_text}")
    else:
        print("\n❌ No response received")

if __name__ == "__main__":
    print("\n🔧 Voice Bot Diagnostics\n")
    
    # Test VM connection
    if not test_vm_connection():
        print("\n❌ VM server is not responding. Please check:")
        print("1. Run 'python server.py' on your VM")
        print("2. Check firewall settings")
        print("3. Verify IP address")
        sys.exit(1)
    
    # Test local components
    test_local_components()
    
    # Test LLM client
    test_llm_client()
    
    print("\n" + "="*60)
    print("✅ Diagnostics complete!")
    print("="*60)