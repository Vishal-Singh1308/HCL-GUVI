from fastapi import FastAPI, UploadFile, File, HTTPException
from tasks import run_analytics_task
import uuid
import redis
import json
import os

app = FastAPI(title="Intelligent Call Center Analytics")
db = redis.Redis(host='localhost', port=6379, db=1)

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    # Save file
    task_id = str(uuid.uuid4())
    file_location = f"temp_{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Trigger async task
    run_analytics_task.delay(task_id, file_location)
    
    return {"task_id": task_id, "message": "Processing started"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    data = db.get(task_id)
    if not data:
        return {"status": "processing"}
    return json.loads(data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
