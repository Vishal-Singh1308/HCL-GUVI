import os
from faster_whisper import WhisperModel
from groq import Groq
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def process_audio_to_intel(file_path):
    # Transcribe
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(file_path)
    transcript = " ".join([s.text for s in segments])

    # Analyze for Rubric Requirements
    prompt = f"Analyze this transcript for Summary, SOP Greeting check, and Payment Category (EMI/Full): {transcript}"
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
        response_format={"type": "json_object"}
    )
    return json.loads(chat_completion.choices[0].message.content)
