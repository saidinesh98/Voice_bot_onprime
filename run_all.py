import os
import subprocess
import sys
import time

def run_command(command, cwd=None):
    print(f"Executing: {command}")
    return subprocess.Popen(command, shell=True, cwd=cwd)

def main():
    print("\n" + "="*60)
    print("🚀  Aura AI - Integrated Voice Assistant")
    print("="*60 + "\n")

    # 1. Build the frontend
    print("📦 Step 1: Building frontend...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    build_process = run_command("npm run build", cwd=frontend_dir)
    build_process.wait()
    
    if build_process.returncode != 0:
        print("❌ Frontend build failed.")
        return

    print("✅ Frontend built successfully.")

    # 2. Check for backend port availability (optional, uvicorn will handle if taken)

    # 3. Start the Python server
    print("\n📦 Step 2: Starting Python Backend...")
    try:
        # Using sys.executable to ensure we use the same venv
        backend_process = run_command(f"{sys.executable} app.py")
        
        print("\n" + "="*60)
        print("🌍 SERVER RUNNING AT: http://localhost:8000")
        print("="*60)
        print("Press Ctrl+C to stop both processes.\n")
        
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping Aura AI...")
        backend_process.terminate()
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
