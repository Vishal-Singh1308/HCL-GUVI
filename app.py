from fastapi import FastAPI, UploadFile, File, HTTPException
from tasks import run_analytics_task
import uuid
import redis
import json
import os
from fastapi import Header, Depends

# 1. This pulls your secret key from Railway's Environment Variables
SECRET_API_KEY = os.getenv("APP_API_KEY", "default_secret_key_123")

# 2. This function checks the 'X-API-KEY' header in the request
def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# 3. Apply it to your upload route
@app.post("/upload")
async def upload_audio(file: UploadFile = File(...), token: str = Depends(verify_api_key)):
    # ... your existing code ...
    return {"task_id": task_id, "message": "Processing started"}
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
