"""
Complaint Service — orchestrates the full complaint lifecycle.

This service layer keeps business logic out of views and models.
It coordinates between apps: complaints, ai_engine, departments, notifications.
"""

from apps.complaints.models import Complaint, StatusUpdate
from apps.ai_engine.classifier import classify_complaint
from apps.ai_engine.router import route_complaint


def create_complaint(complainant, title, description, category=None, address=None,
                     latitude=None, longitude=None, image_path=None):
    """
    Create a new complaint and run the AI pipeline:
    1. Save the complaint
    2. Classify via AI (text + optional image)
    3. Auto-route to the appropriate department
    4. Trigger notifications

    Args:
        complainant: The user submitting the complaint
        title: Complaint title
        description: Detailed description
        category: Optional manual category override
        address: Location address
        latitude: GPS latitude
        longitude: GPS longitude
        image_path: Optional path to uploaded image

    Returns:
        The created Complaint instance
    """
    # Step 1: Run AI classification
    ai_result = classify_complaint(description, image_path)

    # Step 2: Use AI category unless manually overridden
    final_category = category or ai_result.get('category', 'Other')

    # Step 3: Route to department
    department = route_complaint(final_category)

    # Step 4: Create the complaint
    complaint = Complaint.objects.create(
        complainant=complainant,
        title=title,
        description=description,
        category=final_category,
        ai_category=ai_result.get('category'),
        ai_confidence=ai_result.get('confidence'),
        department=department,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )

    # Step 5: Trigger notifications (Phase 10)
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
    old_status = complaint.status
    complaint.status = new_status

    if new_status == Complaint.Status.RESOLVED:
        from django.utils import timezone
        complaint.resolved_at = timezone.now()

    complaint.save()

    status_update = StatusUpdate.objects.create(
        complaint=complaint,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        remarks=remarks,
    )

    # Trigger notification (Phase 10)
    # notify_status_change(complaint, status_update)

    return status_update
