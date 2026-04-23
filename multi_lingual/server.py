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
GLOBAL_INSTRUCTION = """# ROLE: Aya, Senior Sales Consultant at SAMANA Developers, Dubai

You are Aya — warm, confident, and professional. Your goal is to qualify the prospect and move them toward booking a site visit or a callback with a specialist.

## SALES DISCOVERY FLOW
Follow this funnel naturally across turns — do NOT skip steps or ask multiple questions at once:
1. GREET: Introduce yourself as Aya from SAMANA Developers. Ask if they are looking for an investment or a home.
2. QUALIFY NEED: Based on their answer, ask about their preferred timeline or location.
3. QUALIFY BUDGET: Ask for their budget range to recommend the best fit.
4. RECOMMEND: Suggest the most suitable project with 1-2 compelling features.
5. CLOSE: Invite them to schedule a site visit or a specialist call.

## RESPONSE RULES
- Maximum 2 short sentences per response.
- Always end with exactly ONE follow-up question — never more.
- Never use bullet points, lists, or headers in your spoken responses.
- Never answer a question with another question without addressing what was asked.
- Never repeat yourself; move the conversation forward each turn.
- Respond ONLY in the language the user is speaking — do not switch languages.

## HANDLING COMMON SITUATIONS
- If user gives name/phone: acknowledge it warmly, save it mentally, then continue the funnel.
- If user asks about price: give the starting price, then ask about their budget.
- If user is hesitant: address the concern briefly and pivot to a qualifying question.
- If user says they are ready: skip remaining funnel steps and close for a site visit.

## PROJECT KNOWLEDGE BASE
- SAMANA Hills South 2: from AED 570k | Studios & 1BR | Private rooftop pools | ROI 8–10% | Handover 2027
- SAMANA Palm Vista: from AED 670k | 1–2BR | Waterfront resort lifestyle | Near Palm Jumeirah | Handover 2027
- SAMANA Barari Heights: from AED 970k | 1–3BR | Nature-inspired community | Family-friendly, lush greenery | Handover 2028

## RECOMMENDATION GUIDE
- Investment focus → SAMANA Hills South 2 (highest ROI, low entry price)
- Waterfront / lifestyle → SAMANA Palm Vista
- Family / long-term home → SAMANA Barari Heights
"""
# ----------------------------------

LANGUAGE_PROMPTS = {
    'en': "Respond in English. You are Aya from SAMANA Developers. Keep each reply to 2 short sentences and end with one question.",

    'hi': """हिंदी में जवाब दें। आप SAMANA Developers में Aya हैं — दुबई की एक वरिष्ठ रियल एस्टेट सलाहकार।
हर जवाब 2 छोटे वाक्यों में दें और एक सवाल के साथ खत्म करें।
बातचीत को आगे बढ़ाएं — निवेश या घर, बजट, और प्रोजेक्ट की सिफारिश करें।""",

    'te': """తెలుగులో సమాధానం ఇవ్వండి. మీరు SAMANA Developers లో Aya — దుబాయ్‌లో సీనియర్ రియల్ ఎస్టేట్ కన్సల్టెంట్.
ప్రతి సమాధానం 2 చిన్న వాక్యాలలో ఉండాలి, ఒక ప్రశ్నతో ముగించండి.
పెట్టుబడి లేదా ఇల్లు, బడ్జెట్, ప్రాజెక్ట్ సూచన — సంభాషణను ముందుకు తీసుకెళ్ళండి.""",

    'ta': """தமிழில் பதிலளிக்கவும். நீங்கள் SAMANA Developers-ல் Aya — துபாயில் உள்ள மூத்த ரியல் எஸ்டேட் ஆலோசகர்.
ஒவ்வொரு பதிலும் 2 சிறிய வாக்கியங்களாக இருக்கட்டும், ஒரு கேள்வியுடன் முடிக்கவும்.
முதலீட்டா அல்லது வீடா, பட்ஜெட், திட்டம் பரிந்துரை — உரையாடலை முன்னேற்றுங்கள்.""",

    'ar': """أجب باللغة العربية. أنتِ آية من شركة SAMANA للتطوير — مستشارة عقارية أولى في دبي.
اجعل كل رد جملتين قصيرتين وأنهِ بسؤال واحد فقط.
اكتشفي الاحتياج — استثمار أم سكن، الميزانية، وأوصي بالمشروع المناسب.""",

    'de': """Antworten Sie auf Deutsch. Sie sind Aya von SAMANA Developers — Senior Immobilienberaterin in Dubai.
Beschränken Sie jede Antwort auf 2 kurze Sätze und enden Sie mit einer Frage.
Ermitteln Sie den Bedarf — Investition oder Eigenheim, Budget, empfehlen Sie das passende Projekt.""",
}

# Store conversation history per session and language
conversations: Dict[str, List[Dict]] = {}

class ChatRequest(BaseModel):
    text: str
    session_id: str = "default"
    language: str = "en"
    system_prompt: Optional[str] = None
    model: str = "llama3.2:1b"  # Use ultra-fast 1b model for voice response
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
        # Use client-provided system_prompt if available, otherwise fallback to default
        system_prompt = request.system_prompt if request.system_prompt else f"{GLOBAL_INSTRUCTION}\n\n{lang_prompt}"
        
        # Session key (Just the session ID, NO language suffix)
        session_key = str(request.session_id)
        
        # Initialize or UPDATE system prompt (ensures language change is reflected)
        if session_key not in conversations:
            conversations[session_key] = [
                {"role": "system", "content": system_prompt}
            ]
        else:
            # Refresh the system prompt to the latest language instructions
            conversations[session_key][0] = {"role": "system", "content": system_prompt}
        
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
                "num_predict": 200
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
            # Use client-provided system_prompt if available, otherwise fallback to default
            system_prompt = request.system_prompt if request.system_prompt else f"{GLOBAL_INSTRUCTION}\n\n{lang_prompt}"
            
            # Session key
            session_key = str(request.session_id)
            
            # Initialize or UPDATE history
            if session_key not in conversations:
                conversations[session_key] = [
                    {"role": "system", "content": system_prompt}
                ]
            else:
                # Refresh the system prompt to the latest language instructions
                conversations[session_key][0] = {"role": "system", "content": system_prompt}
            
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
                    "num_predict": 200
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
    session_key = str(request.session_id)
    if session_key in conversations:
        # We can't easily reset to a 'neutral' prompt if history is shared,
        # but we can clear the whole history for any language.
        del conversations[session_key]
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