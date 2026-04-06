import os
import base64
import uuid
import whisper
import google.generativeai as genai
from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="HCL Call Center Compliance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
) 
stt_model = whisper.load_model("base")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

VALID_API_KEY = "HCL_VISHAL_2026"

class CallRequest(BaseModel):
    language: str
    audioFormat: str
    audioBase64: str

@app.api_route("/", methods=["GET", "POST"])
async def health_check():
    return {"status": "success", "message": "API is online and ready for HCL evaluation."}

@app.post("/api/call-analytics")
async def process_call_analytics(request: CallRequest, x_api_key: str = Header(None)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    temp_audio = f"{uuid.uuid4()}.mp3"
    try:
        audio_data = base64.b64decode(request.audioBase64)
        with open(temp_audio, "wb") as f:
            f.write(audio_data)

        stt_result = stt_model.transcribe(temp_audio)
        transcript = stt_result['text']

        prompt = f"""
        Analyze this call center transcript: "{transcript}"
        Return a JSON object exactly matching this structure:
        {{
            "summary": "string",
            "sop_validation": {{
                "greeting": bool, "identification": bool, "problemStatement": bool,
                "solutionOffering": bool, "closing": bool, "complianceScore": float,
                "adherenceStatus": "FOLLOWED" or "NOT_FOLLOWED", "explanation": "string"
            }},
            "analytics": {{
                "paymentPreference": "EMI" | "FULL_PAYMENT" | "PARTIAL_PAYMENT" | "DOWN_PAYMENT",
                "rejectionReason": "HIGH_INTEREST" | "BUDGET_CONSTRAINTS" | "ALREADY_PAID" | "NOT_INTERESTED" | "NONE",
                "sentiment": "Positive" | "Negative" | "Neutral"
            }},
            "keywords": ["list", "of", "keywords"]
        }}
        """
        
        raw_response = gemini_model.generate_content(
            prompt, 
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        analysis = raw_response.text

       
        import json
        data = json.loads(analysis)
        
        return {
            "status": "success",
            "language": request.language,
            "transcript": transcript,
            "summary": data["summary"],
            "sop_validation": data["sop_validation"],
            "analytics": data["analytics"],
            "keywords": data["keywords"]
        }

    except Exception as e:
        return {"status": "error", "message": f"Processing failed: {str(e)}"}
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
