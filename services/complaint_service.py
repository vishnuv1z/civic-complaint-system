"""
Complaint Service - orchestrates the full complaint lifecycle.

This service layer keeps business logic out of views and models.
It coordinates between apps: complaints, ai_engine, departments, notifications.
"""

from django.db import transaction
from django.utils import timezone

from apps.ai_engine.classifier import classify_complaint
from apps.ai_engine.router import route_complaint
from apps.complaints.models import Complaint, ComplaintImage, StatusUpdate


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

    The web form and future API endpoints should call this function instead of
    duplicating complaint creation, image saving, AI metadata, and routing.
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
    complaint.save(update_fields=[
        'category',
        'ai_category',
        'ai_confidence',
        'department',
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
