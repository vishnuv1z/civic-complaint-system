"""
Database models for the departments app.

- Department: A government department that handles complaints
- DepartmentStaff: Links staff users to their assigned department
"""

import uuid
from django.db import models
from django.conf import settings


class Department(models.Model):
    """A government department responsible for handling specific complaint categories."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(
        max_length=20, unique=True,
        help_text='Short code, e.g., PWD, WTR, SAN',
    )
    description = models.TextField(blank=True, null=True)
    head_name = models.CharField(max_length=200, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    categories = models.JSONField(
        default=list, blank=True,
        help_text='List of complaint categories this department handles',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f"{self.name} ({self.code})"


class DepartmentStaff(models.Model):
    """Links a staff user to a department with a specific role."""

    class StaffRole(models.TextChoices):
        HEAD = 'head', 'Department Head'
        OFFICER = 'officer', 'Complaint Officer'
        FIELD_WORKER = 'field_worker', 'Field Worker'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='department_assignment',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='staff_members',
    )
    staff_role = models.CharField(
        max_length=20,
        choices=StaffRole.choices,
        default=StaffRole.OFFICER,
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Department Staff'
        verbose_name_plural = 'Department Staff'

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.department.name} ({self.get_staff_role_display()})"
