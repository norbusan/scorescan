from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "scorescan",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.process_score"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minute hard limit
    task_soft_time_limit=540,  # 9 minute soft limit
)
