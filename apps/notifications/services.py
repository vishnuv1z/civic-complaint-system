"""
Notification services — Email and SMS sending functions.
Will be fully implemented in Phase 10.
"""

from django.core.mail import send_mail
from django.conf import settings


def send_email_notification(recipient_email, subject, message):
    """Send an email notification."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def send_sms_notification(phone_number, message):
    """Send an SMS notification via Twilio (Phase 10)."""
    # Twilio integration will be added in Phase 10
    pass
