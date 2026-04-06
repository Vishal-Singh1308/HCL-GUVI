import os
import base64
import uuid
import json
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from faster_whisper import WhisperModel
from groq import Groq

app = FastAPI(title="HCL High-Precision Analytics API")

# Enable CORS for the HCL Tester
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

stt_model = WhisperModel("base", device="cpu", compute_type="int8")

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

VALID_API_KEY = "HCL_VISHAL_2026"

class CallRequest(BaseModel):
    language: str
    audioFormat: str
    audioBase64: str

@app.api_route("/", methods=["GET", "POST"])
async def root_verification():
    return {"status": "online", "message": "HCL Compliance API Active"}

@app.post("/api/call-analytics")
async def process_call_analytics(request: CallRequest, x_api_key: str = Header(None)):
    # 1. API Authentication [cite: 8-11]
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    temp_audio = f"{uuid.uuid4()}.mp3"
    try:
        # 2. Decode Base64 Audio [cite: 5, 24]
        audio_data = base64.b64decode(request.audioBase64)
        with open(temp_audio, "wb") as f:
            f.write(audio_data)

        segments, info = stt_model.transcribe(temp_audio, beam_size=5)
        transcript_text = " ".join([segment.text for segment in segments])

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a call center compliance auditor. Output ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": f"""Analyze this transcript: "{transcript_text}"
                    Return this JSON structure EXACTLY:
                    {{
                        "summary": "concise summary",
                        "sop_validation": {{
                            "greeting": bool, "identification": bool, "problemStatement": bool,
                            "solutionOffering": bool, "closing": bool, "complianceScore": float,
                            "adherenceStatus": "FOLLOWED" or "NOT_FOLLOWED", "explanation": "string"
                        }},
                        "analytics": {{
                            "paymentPreference": "EMI"|"FULL_PAYMENT"|"PARTIAL_PAYMENT"|"DOWN_PAYMENT",
                            "rejectionReason": "HIGH_INTEREST"|"BUDGET_CONSTRAINTS"|"ALREADY_PAID"|"NOT_INTERESTED"|"NONE",
                            "sentiment": "Positive"|"Negative"|"Neutral"
                        }},
                        "keywords": ["list"]
                    }}"""
                }
            ],
            model="llama3-70b-8192",
            response_format={"type": "json_object"}
        )

        analysis = json.loads(chat_completion.choices[0].message.content)

        return {
            "status": "success",
            "language": request.language,
            "transcript": transcript_text,
            "summary": analysis["summary"],
            "sop_validation": analysis["sop_validation"],
            "analytics": analysis["analytics"],
            "keywords": analysis["keywords"]
        }

    except Exception as e:
        return {"status": "error", "message": f"Pipeline failure: {str(e)}"}
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
