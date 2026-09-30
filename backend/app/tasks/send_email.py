from app.tasks import celery_app
from app.services.email import email_service


@celery_app.task(name="send_password_reset_email")
def send_password_reset_email_task(to_email: str, reset_token: str) -> bool:
    """Send the password reset email outside the request cycle."""
    return email_service.send_password_reset_email(to_email, reset_token)
