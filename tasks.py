import os
from celery import Celery
import redis
import json
from models import process_audio_to_intel

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL)
db = redis.Redis.from_url(REDIS_URL)

@celery_app.task(name="tasks.run_analytics_task")
def run_analytics_task(task_id, file_path):
    try:
        # This calls the AI logic from your models file
        analysis_results = process_audio_to_intel(file_path)
        db.set(task_id, json.dumps(analysis_results))
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        db.set(task_id, json.dumps({"status": "failed", "error": str(e)}))
