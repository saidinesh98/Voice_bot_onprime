# test_vm_direct.py - Test VM server directly
import requests
import json

VM_IP = "172.20.100.68"
VM_PORT = 8000

print(f"Testing VM Server at http://{VM_IP}:{VM_PORT}\n")

# Test health endpoint
try:
    response = requests.get(f"http://{VM_IP}:{VM_PORT}/health", timeout=5)
    print(f"Health check: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Health check failed: {e}")

print("\n" + "="*50)

# Test chat endpoint
test_message = "Tell me about Eshunt"
print(f"Sending: '{test_message}'")

try:
    response = requests.post(
        f"http://{VM_IP}:{VM_PORT}/chat",
        json={"text": test_message, "session_id": "test"},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result.get('response', 'No response field')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")