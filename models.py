import os
from faster_whisper import WhisperModel
import json
from groq import Groq # Using Groq for high-speed analysis
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Whisper (using 'base' for speed, swap to 'large-v3' for high-end accuracy)
model = WhisperModel("base", device="cpu", compute_type="int8")
client = Groq(api_key=API_KEY)
def process_audio_to_intel(file_path):
    # 1. Transcription
    segments, _ = model.transcribe(file_path, beam_size=5)
    transcript = " ".join([s.text for s in segments])

    # 2. High-End Analysis Prompt
    prompt = f"""
    Analyze this call transcript: "{transcript}"
    Strictly output ONLY JSON with this format:
    {{
      "summary": "Short English summary",
      "sop_validation": {{
          "greeting": true/false,
          "brand_mention": true/false,
          "closing": true/false
      }},
      "payment_category": "EMI / Full Payment / Partial Payment / Down Payment / None",
      "rejection_reason": "Categorize why the customer refused, if applicable",
      "keywords": ["list", "of", "important", "terms"]
    }}
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    
    return transcript, json.loads(response.choices[0].message.content)
