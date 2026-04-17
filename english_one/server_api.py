#!/usr/bin/env python3
"""
Voice Bot Server - Runs on VM with Ollama
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime

app = FastAPI(title="Voice Bot Server", version="1.0")

# Enable CORS for local laptop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific IP in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DEFAULT_MODEL = "llama3.2:3b"  # Fast model
SYSTEM_PROMPT = """# ROLE: Senior Property Consultant @ SAMANA Developers
You are a high-end, charismatic, and knowledgeable human sales consultant. You don't "process" requests—you have conversations. 

-keep the response short and concise.

# PERSONALITY & "SMART" SPEECH PATTERNS
- ACTIVE ACKNOWLEDGMENT: Before answering, validate the user. Use phrases like "I hear you," "That's a popular choice," or "I see what you're looking for."
- CONVERSATIONAL FILLERS: Sprinkle in natural human fillers like "Well," "Actually," or "To be honest" at the start of sentences to break the robotic flow.
- THE "GENTLE REDIRECT": If a user asks for a location SAMANA doesn't have, don't say "No." Say, "That's a great area, though many of our clients who looked there actually ended up choosing [Project Name] because of the better ROI. Have you seen that one?"
- BREVITY IS LUXURY: Keep responses to 1-2 sentences. Let the user breathe.

# THE FLOW (STRICT ORDER)
1. GREETING & DISCOVERY: 
   - Warm welcome + ONLY ONE question (Budget OR Location OR Purpose).
   - *Example:* "Hi! Thanks for reaching out to SAMANA. Just to make sure I’m looking at the right inventory for you, are you exploring for your own home or as an investment?"

2. INTELLIGENT SUGGESTIONS:
   - Suggest 2–3 properties ONLY after the user answers discovery.
   - Format: [Project Name] — [Location] — [Price] — [Human Highlight].
   - *Smart Mapping:* - Marina/JBR → SAMANA Palm Vista (Waterfront vibe).
     - Downtown/Business Bay → Arjan projects (Better value, similar luxury).
     - Peaceful/Nature → SAMANA Barari Heights or Greens.

3. CLOSING & LEAD CAPTURE:
   - Only when interest is high, ask: "I’d love to send you the floor plans and the latest offer. What’s the best WhatsApp number to reach you on?"
   - Final phrase: "Thank you for your time, it was great speaking with you, Our team will contact you soon."

# PRICING & LANGUAGE
- CURRENCY: Always AED. Never say "Dollars."
- LANGUAGE: Lock to the user's first message (English or Arabic). Never mix.

# PROJECT DATABASE
- SAMANA Hills South 2 | Arjan | AED 570,000 | Private pools in every unit.
- SAMANA Barari Heights | Majan | AED 970,000 | Nature-inspired luxury living.
- SAMANA Palm Vista | Dubai Islands | AED 670,000 | Stunning waterfront views.
- SAMANA Creek Horizon | Dubai Creek | AED 370,000 | Incredible entry point for investors.
- SAMANA Sky Views | Arjan | AED 680,000 | Iconic architecture that stands out.
- SAMANA Golf Avenue | Studio City | AED 650,000 | Perfect for a resort-style lifestyle.
- SAMANA Golf Views | Sports City | AED 720,000 | Overlooks world-class golf courses.
- SAMANA Greens | Arjan | AED 550,000 | Sustainable, eco-friendly community.

# FAILSAFES
- ONE QUESTION MAX: Never ask two things at once.
- MINIMALISM: Do not explain amenities or ROI unless they ask "Why this one?" or "Tell me more."""

# Store conversation history per session
conversations: Dict[str, List[Dict]] = {}

class ChatRequest(BaseModel):
    text: str
    session_id: str = "default"
    model: Optional[str] = DEFAULT_MODEL

class ClearRequest(BaseModel):
    session_id: str = "default"

@app.get("/")
def root():
    return {"status": "online", "service": "Voice Bot Server"}

@app.get("/health")
def health():
    """Health check endpoint"""
    try:
        ollama.list()
        return {"status": "healthy", "ollama": "connected"}
    except:
        return {"status": "degraded", "ollama": "disconnected"}

@app.post("/chat")
def chat(request: ChatRequest):
    """Non-streaming chat endpoint"""
    try:
        # Get or create conversation history
        if request.session_id not in conversations:
            conversations[request.session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        
        # Add user message
        conversations[request.session_id].append(
            {"role": "user", "content": request.text}
        )
        
        # Get response from Ollama
        response = ollama.chat(
            model=request.model,
            messages=conversations[request.session_id],
            options={
                "temperature": 0.3,
                "num_predict": 100
            }
        )
        
        assistant_response = response['message']['content']
        
        # Add to history
        conversations[request.session_id].append(
            {"role": "assistant", "content": assistant_response}
        )
        
        # Keep history manageable (last 10 exchanges)
        if len(conversations[request.session_id]) > 21:
            conversations[request.session_id] = [
                conversations[request.session_id][0]
            ] + conversations[request.session_id][-20:]
        
        return {
            "response": assistant_response,
            "session_id": request.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint - returns Server-Sent Events"""
    from fastapi.responses import StreamingResponse
    
    async def generate():
        try:
            # Get or create conversation history
            if request.session_id not in conversations:
                conversations[request.session_id] = [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ]
            
            # Add user message
            conversations[request.session_id].append(
                {"role": "user", "content": request.text}
            )
            
            # Stream from Ollama
            stream = ollama.chat(
                model=request.model,
                messages=conversations[request.session_id],
                stream=True,
                options={
                    "temperature": 0.3,
                    "num_predict": 100
                }
            )
            
            full_response = ""
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    token = chunk['message']['content']
                    full_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
            
            # Save to history
            conversations[request.session_id].append(
                {"role": "assistant", "content": full_response}
            )
            
            # Trim history if needed
            if len(conversations[request.session_id]) > 21:
                conversations[request.session_id] = [
                    conversations[request.session_id][0]
                ] + conversations[request.session_id][-20:]
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/clear")
def clear_history(request: ClearRequest):
    """Clear conversation history for a session"""
    if request.session_id in conversations:
        conversations[request.session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        return {"status": "cleared", "session_id": request.session_id}
    return {"status": "not_found", "session_id": request.session_id}

@app.get("/models")
def list_models():
    """List available Ollama models"""
    try:
        models = ollama.list()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("🚀 Voice Bot Server Starting...")
    print("="*60)
    print(f"Server will run on: http://0.0.0.0:8000")
    print(f"API Docs: http://0.0.0.0:8000/docs")
    print("="*60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )