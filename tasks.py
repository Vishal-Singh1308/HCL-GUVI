from celery import Celery
from models import process_audio_to_intel
import redis
import json

celery_app = Celery('tasks', broker='redis://localhost:6379/0')
db = redis.Redis(host='localhost', port=6379, db=1)

@celery_app.task
def run_analytics_task(task_id, file_path):
    try:
        transcript, analysis = process_audio_to_intel(file_path)
        result = {
            "status": "completed",
            "transcript": transcript,
            "analysis": analysis
        }
        db.set(task_id, json.dumps(result))
    except Exception as e:
        db.set(task_id, json.dumps({"status": "failed", "error": str(e)}))
