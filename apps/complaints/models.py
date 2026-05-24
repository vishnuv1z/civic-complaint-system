"""
Database models for the complaints app.

Core models:
- Complaint: The main complaint submitted by a citizen
- ComplaintImage: Images attached to a complaint
- StatusUpdate: Timeline of status changes
"""

import uuid
from django.db import models
from django.conf import settings


class Complaint(models.Model):
    """A civic complaint submitted by a citizen via text or image."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under Review'
        FORWARDED = 'forwarded', 'Forwarded to Authority'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        REJECTED = 'rejected', 'Rejected'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracking_id = models.CharField(
        max_length=20, unique=True, editable=False,
        help_text='Public tracking ID for citizens (e.g., CMP-20260511-A1B2)',
    )
    complainant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints',
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='AI-assigned or manually selected category',
    )
    ai_category = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='Category predicted by the AI engine',
    )
    ai_confidence = models.FloatField(
        blank=True, null=True,
        help_text='AI confidence score (0.0 – 1.0)',
    )
    ai_genuineness_score = models.FloatField(
        blank=True, null=True,
        help_text='AI confidence that this is a genuine civic complaint',
    )
    ai_genuineness_reason = models.TextField(blank=True, null=True)
    ai_validation_flags = models.JSONField(default=list, blank=True)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='complaints',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    # Location fields (Phase 13)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'

    def __str__(self):
        return f"[{self.tracking_id}] {self.title}"

    def save(self, *args, **kwargs):
        """Auto-generate tracking_id on first save."""
        if not self.tracking_id:
            import random
            import string
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.tracking_id = f"CMP-{date_str}-{random_suffix}"
        super().save(*args, **kwargs)


class ComplaintImage(models.Model):
    """Images attached to a complaint (supports AI image analysis)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='complaints/images/%Y/%m/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Image for {self.complaint.tracking_id}"


class StatusUpdate(models.Model):
    """Timeline entry tracking status changes on a complaint."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='status_updates',
    )
    old_status = models.CharField(max_length=20, choices=Complaint.Status.choices)
    new_status = models.CharField(max_length=20, choices=Complaint.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint.tracking_id}: {self.old_status} → {self.new_status}"
class ComplaintForwardLog(models.Model):
    """Audit trail for complaints forwarded to official authority contacts."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='forward_logs',
    )
    forwarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='complaint_forward_logs',
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaint_forward_logs',
    )
    recipient_email = models.EmailField(blank=True, null=True)
    recipient_phone = models.CharField(max_length=15, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Complaint Forward Log'
        verbose_name_plural = 'Complaint Forward Logs'

    def __str__(self):
        return f"{self.complaint.tracking_id} -> {self.recipient_email or 'no email'}"
