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
    # Must exceed the sum of the per-step timeouts: Audiveris (5 min),
    # oemer fallback (10 min) and MuseScore (2 min), plus preprocessing.
    task_time_limit=1560,  # 26 minute hard limit
    task_soft_time_limit=1500,  # 25 minute soft limit
)
