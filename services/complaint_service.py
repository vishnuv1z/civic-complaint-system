"""
Complaint Service - orchestrates the full complaint lifecycle.

This service layer keeps business logic out of views and models.
It coordinates between apps: complaints, ai_engine, departments, notifications.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.ai_engine.classifier import classify_complaint
from apps.ai_engine.router import route_complaint
from apps.notifications.services import send_sms_notification
from apps.complaints.models import (
    Complaint,
    ComplaintForwardLog,
    ComplaintImage,
    StatusUpdate,
)


HIGH_PRIORITY_CATEGORIES = {
    'Electricity',
    'Drainage & Sewage',
    'Public Safety',
    'Traffic Signal',
}

MEDIUM_PRIORITY_CATEGORIES = {
    'Road & Pothole',
    'Water Supply',
    'Garbage & Sanitation',
    'Street Light',
    'Public Transport',
    'Illegal Construction',
}

CRITICAL_KEYWORDS = {
    'accident',
    'collapse',
    'danger',
    'electrocution',
    'emergency',
    'fire',
    'injury',
    'live wire',
    'life threatening',
    'severe',
}

HIGH_KEYWORDS = {
    'blocked',
    'burst',
    'contaminated',
    'flood',
    'hazard',
    'overflow',
    'school',
    'urgent',
}


def assign_priority(category, title='', description=''):
    """Assign initial complaint priority from category and seriousness keywords."""
    text = f"{title or ''} {description or ''}".lower()

    if any(keyword in text for keyword in CRITICAL_KEYWORDS):
        return Complaint.Priority.CRITICAL

    if any(keyword in text for keyword in HIGH_KEYWORDS):
        return Complaint.Priority.HIGH

    if category in HIGH_PRIORITY_CATEGORIES:
        return Complaint.Priority.HIGH

    if category in MEDIUM_PRIORITY_CATEGORIES:
        return Complaint.Priority.MEDIUM

    return Complaint.Priority.LOW


def create_complaint(
    complainant,
    title,
    description,
    category=None,
    address=None,
    latitude=None,
    longitude=None,
    image_file=None,
    image_caption=None,
    image_path=None,
    run_ai=True,
):
    """
    Create a complaint and keep the full creation workflow in one place.

    Complaints enter the department triage queue only. They are not sent to
    authority contacts until department staff reviews and forwards them.
    """
    initial_category = category or 'Other'
    saved_image = None

    with transaction.atomic():
        complaint = Complaint.objects.create(
            complainant=complainant,
            title=title,
            description=description,
            category=initial_category,
            department=route_complaint(initial_category),
            priority=assign_priority(initial_category, title, description),
            address=address,
            latitude=latitude,
            longitude=longitude,
        )

        if image_file:
            saved_image = ComplaintImage.objects.create(
                complaint=complaint,
                image=image_file,
                caption=image_caption,
            )

    ai_result = {}
    if run_ai:
        classification_image_path = image_path

        if not classification_image_path and saved_image:
            try:
                classification_image_path = saved_image.image.path
            except (NotImplementedError, ValueError):
                classification_image_path = None

        ai_result = classify_complaint(description, classification_image_path)

    ai_category = ai_result.get('category')
    final_category = category or ai_category or 'Other'

    complaint.category = final_category
    complaint.ai_category = ai_category
    complaint.ai_confidence = ai_result.get('confidence')
    complaint.department = route_complaint(final_category)
    complaint.priority = assign_priority(final_category, title, description)
    complaint.save(update_fields=[
        'category',
        'ai_category',
        'ai_confidence',
        'department',
        'priority',
        'updated_at',
    ])

    # Notifications will be wired here in the notification workflow step.
    # notify_complaint_created(complaint)

    return complaint


def update_complaint_status(complaint, new_status, changed_by, remarks=None):
    """
    Update a complaint's status and create a timeline entry.

    Args:
        complaint: The Complaint instance
        new_status: New status value
        changed_by: The user making the change
        remarks: Optional remarks about the status change

    Returns:
        The created StatusUpdate instance
    """
    valid_statuses = {status for status, _ in Complaint.Status.choices}
    if new_status not in valid_statuses:
        raise ValueError(f"'{new_status}' is not a valid complaint status.")

    old_status = complaint.status

    with transaction.atomic():
        complaint.status = new_status

        if new_status == Complaint.Status.RESOLVED:
            complaint.resolved_at = timezone.now()
        elif old_status == Complaint.Status.RESOLVED:
            complaint.resolved_at = None

        complaint.save(update_fields=['status', 'resolved_at', 'updated_at'])

        status_update = StatusUpdate.objects.create(
            complaint=complaint,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            remarks=remarks,
        )

    # Notifications will be wired here in the notification workflow step.
    # notify_status_change(complaint, status_update)

    return status_update


def build_authority_forward_message(complaint, remarks=''):
    """Build the email body sent after department staff triage."""
    location_lines = []
    if complaint.address:
        location_lines.append(f"Address: {complaint.address}")
    if complaint.latitude is not None and complaint.longitude is not None:
        location_lines.append(f"Coordinates: {complaint.latitude}, {complaint.longitude}")

    image_lines = [
        image.image.url for image in complaint.images.all()
        if image.image
    ]

    lines = [
        f"Tracking ID: {complaint.tracking_id}",
        f"Title: {complaint.title}",
        f"Category: {complaint.category or 'Uncategorized'}",
        f"Priority: {complaint.get_priority_display()}",
        f"Submitted On: {complaint.created_at:%Y-%m-%d %H:%M}",
        "",
        "Description:",
        complaint.description,
    ]

    if location_lines:
        lines.extend(["", "Location:", *location_lines])

    if image_lines:
        lines.extend(["", "Attached image links:", *image_lines])

    if remarks:
        lines.extend(["", "Department triage remarks:", remarks])

    return "\n".join(lines)


def forward_complaint_to_authority(complaint, forwarded_by, remarks=''):
    """
    Send a reviewed complaint to the assigned department authority contact.

    The complaint is marked forwarded only after the authority email or SMS succeeds.
    """
    department = complaint.department

    if not department:
        raise ValueError('This complaint is not assigned to a department.')

    if not department.contact_email and not department.contact_phone:
        raise ValueError('The assigned department has no authority email or phone configured.')

    subject = f"Reviewed civic complaint {complaint.tracking_id}: {complaint.title}"
    message = build_authority_forward_message(complaint, remarks)

    forward_log = ComplaintForwardLog.objects.create(
        complaint=complaint,
        forwarded_by=forwarded_by,
        department=department,
        recipient_email=department.contact_email,
        recipient_phone=department.contact_phone,
        subject=subject,
        message=message,
        remarks=remarks,
    )

    email_sent = False
    sms_sent = False
    error_msgs = []

    if department.contact_email:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[department.contact_email],
                fail_silently=False,
            )
            email_sent = True
        except Exception as exc:
            error_msgs.append(f"Email error: {str(exc)}")

    if department.contact_phone:
        sms_parts = [
            f"Civic Complaint {complaint.tracking_id}: {complaint.title}",
            f"Priority: {complaint.get_priority_display()}",
            f"Desc: {complaint.description}"
        ]
        
        if complaint.address:
            sms_parts.append(f"Loc: {complaint.address}")
        elif complaint.latitude is not None and complaint.longitude is not None:
            sms_parts.append(f"Loc: {complaint.latitude}, {complaint.longitude}")
            
        sms_msg = "\n".join(sms_parts)

        if send_sms_notification(department.contact_phone, sms_msg):
            sms_sent = True
        else:
            error_msgs.append("SMS error: Failed to send via Twilio")

    if not email_sent and not sms_sent:
        forward_log.status = ComplaintForwardLog.Status.FAILED
        forward_log.error_message = " | ".join(error_msgs)
        forward_log.save(update_fields=['status', 'error_message'])
        raise ValueError(f"Failed to route complaint: {forward_log.error_message}")

    forward_log.status = ComplaintForwardLog.Status.SENT
    forward_log.sent_at = timezone.now()
    if error_msgs:
        forward_log.error_message = "Partial success. " + " | ".join(error_msgs)
        forward_log.save(update_fields=['status', 'sent_at', 'error_message'])
    else:
        forward_log.save(update_fields=['status', 'sent_at'])

    update_complaint_status(
        complaint=complaint,
        new_status=Complaint.Status.FORWARDED,
        changed_by=forwarded_by,
        remarks=remarks or 'Forwarded to official authority contact.',
    )

    complaint.refresh_from_db()
    return forward_log
