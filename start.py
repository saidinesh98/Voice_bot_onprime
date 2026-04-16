#!/usr/bin/env python3
"""
Windows Voice Bot Launcher
"""
import subprocess
import sys
import os
import time
import requests
import json

def print_banner():
    print("\n" + "="*60)
    print("🎙️  VOICE BOT - Windows Edition")
    print("="*60)
    print("Split Architecture: Local Audio + VM LLM")
    print("="*60 + "\n")

def check_dependencies():
    """Check if required packages are installed"""
    required = ['sounddevice', 'numpy', 'faster_whisper', 'pyttsx3', 'requests']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        install = input("Install missing packages? (y/n): ")
        if install.lower() == 'y':
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing)
        else:
            return False
    
    return True

def test_microphone():
    """Test if microphone is working"""
    try:
        import sounddevice as sd
        import numpy as np
        
        print("\n🎤 Testing microphone...")
        input("Press Enter and speak for 2 seconds...")
        
        duration = 2
        recording = sd.rec(int(duration * 16000), 
                          samplerate=16000, 
                          channels=1, 
                          dtype='float32')
        sd.wait()
        
        energy = np.sqrt(np.mean(recording**2))
        print(f"Audio level: {energy:.4f}")
        
        if energy > 0.005:
            print("✅ Microphone working!")
            return True
        else:
            print("❌ No sound detected. Check your microphone.")
            return False
            
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if microphone is connected")
        print("2. Check Windows privacy settings")
        print("3. Run: python -m sounddevice")
        return False

def test_vm_connection(vm_ip, vm_port=8000):
    """Test connection to VM server"""
    try:
        url = f"http://{vm_ip}:{vm_port}/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Connected to VM at {vm_ip}:{vm_port}")
            return True
        else:
            print(f"⚠️  VM responded but not healthy")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {vm_ip}:{vm_port}")
        print("\nCheck:")
        print("1. Is VM server running?")
        print("2. Is the IP correct?")
        print("3. Is port 8000 open?")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def create_config(vm_ip, vm_port=8000):
    """Create config file"""
    config = {
        "server_url": f"http://{vm_ip}:{vm_port}",
        "session_id": "windows_client",
        "model": "llama3.2:3b"
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Config saved to config.json")

def load_config():
    """Load config file"""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        return None

def main():
    print_banner()
    
    # Check Python
    print(f"🐍 Python: {sys.version}")
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing packages and try again")
        return
    
    # Load or create config
    config = load_config()
    
    if config:
        print(f"\n📋 Loaded config: Server at {config['server_url']}")
        use_existing = input("Use existing config? (y/n): ")
        if use_existing.lower() != 'y':
            config = None
    
    if not config:
        # Get VM IP
        print("\n🖥️  VM Server Configuration")
        print("-" * 40)
        vm_ip = input("Enter VM IP address (e.g., 192.168.1.100): ").strip()
        vm_port = input("Enter VM port [8000]: ").strip()
        vm_port = int(vm_port) if vm_port else 8000
        
        # Test connection
        if not test_vm_connection(vm_ip, vm_port):
            retry = input("\nContinue anyway? (y/n): ")
            if retry.lower() != 'y':
                return
        
        create_config(vm_ip, vm_port)
    
    # Test microphone
    print("\n🎙️  Microphone Setup")
    print("-" * 40)
    test_microphone()
    
    # Download STT model if not exists
    print("\n📥 Checking STT model...")
    from faster_whisper import WhisperModel
    try:
        model = WhisperModel('small.en', device='cpu', compute_type='int8')
        print("✅ STT model ready")
    except:
        print("⚠️  Downloading STT model (first time may take a few minutes)...")
        model = WhisperModel('small.en', device='cpu', compute_type='int8')
    
    # Run main bot
    print("\n" + "="*60)
    print("🚀 Starting Voice Bot...")
    print("="*60)
    print("\nCommands:")
    print("  • Speak naturally into your microphone")
    print("  • Say 'quit', 'exit', or 'goodbye' to stop")
    print("  • Say 'clear memory' to reset conversation")
    print("-"*60 + "\n")
    
    # Import and run main
    from main import main as run_bot
    run_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPress Enter to exit...")
        input()