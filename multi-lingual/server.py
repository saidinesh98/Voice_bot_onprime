#!/usr/bin/env python3
"""
Voice Bot Server - Multi-Lingual Version
Run this on your VM at 172.20.100.68:8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import ollama
import json
from typing import Optional, Dict, List

app = FastAPI(title="Multi-Lingual Voice Bot Server", version="2.0")

# Enable CORS for your local laptop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your laptop IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# MULTI-LINGUAL SYSTEM PROMPTS
# ============================================

# --- EDIT THIS FOR GLOBAL RULES ---
GLOBAL_INSTRUCTION = """# ROLE: Senior Property Consultant @ SAMANA Developers
You are a high-end, charismatic, and knowledgeable human sales consultant. 
You don't "process" requests—you have conversations. 

- Keep responses short and concise (1-3 sentences maximum).
- Always use AED for pricing (Never say "Dollars").
- Use a friendly, professional tone."""
# ----------------------------------

LANGUAGE_PROMPTS = {
    'en': """You are a helpful, conversational voice assistant. 
Keep responses:
- Short and punchy (1-3 sentences maximum)
- Natural for spoken conversation
- Friendly and engaging
- Answer directly without preamble""",

    'hi': """आप एक सहायक आवाज सहायक हैं।
अपने उत्तर छोटे और संक्षिप्त रखें (अधिकतम 1-3 वाक्य)।
बातचीत के लिए प्राकृतिक और मैत्रीपूर्ण रहें।
सीधे और स्पष्ट उत्तर दें।""",

    'ta': """நீங்கள் ஒரு உதவியான குரல் உதவியாளர்.
பதில்களை குறுகியதாக வையுங்கள் (அதிகபட்சம் 1-3 வாக்கியங்கள்).
பேச்சுக்கு இயற்கையாகவும் நட்பாகவும் இருங்கள்.
நேரடியாக பதிலளிக்கவும்.""",

    'te': """మీరు సహాయకారి వాయిస్ అసిస్టెంట్.
సమాధానాలు చిన్నగా ఉంచండి (గరిష్టంగా 1-3 వాక్యాలు).
సంభాషణకు సహజంగా ఉండండి.
నేరుగా సమాధానం ఇవ్వండి.""",

    'ml': """നിങ്ങൾ ഒരു സഹായകരമായ വോയ്സ് അസിസ്റ്റന്റാണ്.
ഉത്തരങ്ങൾ ചെറുതായി സൂക്ഷിക്കുക (പരമാവധി 1-3 വാക്യങ്ങൾ).
സംഭാഷണത്തിന് സ്വാഭാവികമായിരിക്കുക.
നേരിട്ട് ഉത്തരം നൽകുക.""",

    'bn': """আপনি একজন সহায়ক ভয়েস সহায়ক।
উত্তর ছোট রাখুন (সর্বোচ্চ 1-3 বাক্য)।
কথোপকথনের জন্য স্বাভাবিক থাকুন।
সরাসরি উত্তর দিন।""",

    'fr': """Vous êtes un assistant vocal utile.
Gardez les réponses courtes (1-3 phrases maximum).
Soyez naturel pour la conversation parlé.
Répondez directement sans préambule.""",

    'de': """Sie sind ein hilfsbereiter Sprachassistent.
Halten Sie Antworten kurz (maximal 1-3 Sätze).
Seien Sie natürlich für gesprochene Konversation.
Antworten Sie direkt ohne Umschweife.""",

    'es': """Eres un asistente de voz útil.
Mantén las respuestas cortas (1-3 oraciones como máximo).
Sé natural para la conversación hablada.
Responde directamente sin preámbulos.""",

    'zh': """你是一个有帮助的语音助手。
保持回答简短（最多1-3句话）。
对话要自然。
直接回答，不要铺垫。""",

    'ja': """あなたは役立つ音声アシスタントです。
回答は短くしてください（最大1-3文）。
会話は自然に。
前置きなしで直接答えてください。""",

    'ru': """Вы полезный голосовой помощник.
Держите ответы короткими (максимум 1-3 предложения).
Будьте естественны для разговорной речи.
Отвечайте прямо без предисловий.""",

    'ar': """أنت مساعد صوتي مفيد.
اجعل الإجابات قصيرة (1-3 جمل كحد أقصى).
كن طبيعياً في المحادثة المنطوقة.
أجب مباشرة بدون مقدمات."""

}

# Store conversation history per session and language
conversations: Dict[str, List[Dict]] = {}

class ChatRequest(BaseModel):
    text: str
    session_id: str = "default"
    language: str = "en"
    model: str = "llama3.2:3b"  # Use fast model
    temperature: float = 0.3

class ClearRequest(BaseModel):
    session_id: str = "default"
    language: Optional[str] = None

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Multi-Lingual Voice Bot Server",
        "supported_languages": list(LANGUAGE_PROMPTS.keys())
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    try:
        ollama.list()
        return {
            "status": "healthy",
            "ollama": "connected",
            "languages_available": len(LANGUAGE_PROMPTS)
        }
    except Exception as e:
        return {"status": "degraded", "ollama": "disconnected", "error": str(e)}

@app.get("/languages")
def get_languages():
    """Get list of supported languages"""
    return {"languages": list(LANGUAGE_PROMPTS.keys())}

@app.post("/chat")
def chat(request: ChatRequest):
    """Non-streaming chat endpoint"""
    try:
        # Get language-specific prompt
        lang_prompt = LANGUAGE_PROMPTS.get(
            request.language,
            LANGUAGE_PROMPTS['en']  # Fallback to English
        )
        system_prompt = f"{GLOBAL_INSTRUCTION}\n\n{lang_prompt}"
        
        # Create session key (includes language for separate histories)
        session_key = f"{request.session_id}_{request.language}"
        
        # Initialize conversation history
        if session_key not in conversations:
            conversations[session_key] = [
                {"role": "system", "content": system_prompt}
            ]
        
        # Add user message
        conversations[session_key].append(
            {"role": "user", "content": request.text}
        )
        
        # Get response from Ollama
        response = ollama.chat(
            model=request.model,
            messages=conversations[session_key],
            options={
                "temperature": request.temperature,
                "num_predict": 100
            }
        )
        
        assistant_response = response['message']['content']
        
        # Add to history
        conversations[session_key].append(
            {"role": "assistant", "content": assistant_response}
        )
        
        # Keep history manageable (system + last 10 exchanges)
        if len(conversations[session_key]) > 21:
            conversations[session_key] = [
                conversations[session_key][0]  # Keep system prompt
            ] + conversations[session_key][-20:]  # Last 10 exchanges
        
        return {
            "response": assistant_response,
            "session_id": request.session_id,
            "language": request.language
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint for real-time responses"""
    
    async def generate():
        try:
            # Get language-specific prompt
            lang_prompt = LANGUAGE_PROMPTS.get(
                request.language,
                LANGUAGE_PROMPTS['en']
            )
            system_prompt = f"{GLOBAL_INSTRUCTION}\n\n{lang_prompt}"
            
            # Session key
            session_key = f"{request.session_id}_{request.language}"
            
            # Initialize history
            if session_key not in conversations:
                conversations[session_key] = [
                    {"role": "system", "content": system_prompt}
                ]
            
            # Add user message
            conversations[session_key].append(
                {"role": "user", "content": request.text}
            )
            
            # Stream from Ollama
            stream = ollama.chat(
                model=request.model,
                messages=conversations[session_key],
                stream=True,
                options={
                    "temperature": request.temperature,
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
            conversations[session_key].append(
                {"role": "assistant", "content": full_response}
            )
            
            # Trim history
            if len(conversations[session_key]) > 21:
                conversations[session_key] = [
                    conversations[session_key][0]
                ] + conversations[session_key][-20:]
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/clear")
def clear_history(request: ClearRequest):
    """Clear conversation history"""
    if request.language:
        session_key = f"{request.session_id}_{request.language}"
        if session_key in conversations:
            lang_prompt = LANGUAGE_PROMPTS.get(request.language, LANGUAGE_PROMPTS['en'])
            system_prompt = f"{GLOBAL_INSTRUCTION}\n\n{lang_prompt}"
            conversations[session_key] = [
                {"role": "system", "content": system_prompt}
            ]
            return {"status": "cleared", "session": session_key}
    else:
        # Clear all sessions for this session_id
        keys_to_delete = [k for k in conversations if k.startswith(request.session_id)]
        for key in keys_to_delete:
            del conversations[key]
        return {"status": "cleared", "sessions": len(keys_to_delete)}
    
    return {"status": "not_found"}

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🌍 MULTI-LINGUAL VOICE BOT SERVER")
    print("="*60)
    print(f"Supported Languages: {len(LANGUAGE_PROMPTS)}")
    print("  - English, Hindi, Tamil, Telugu, Malayalam, Bengali")
    print("  - French, German, Spanish, Chinese, Japanese, Russian")
    print("  - Arabic (MSA, Egyptian, Saudi, Levantine)")
    print("="*60)
    print(f"Server running on: http://0.0.0.0:8000")
    print(f"API Docs: http://0.0.0.0:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )