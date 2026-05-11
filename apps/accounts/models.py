"""
Custom User model for the Civic Complaint Management System.

Uses email as the primary login field. Supports multiple user roles:
- CITIZEN: Regular users who submit complaints
- DEPARTMENT_STAFF: Government employees who handle complaints
- ADMIN: System administrators
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """Extended user model with email-based authentication and role support."""

    class Role(models.TextChoices):
        CITIZEN = 'citizen', 'Citizen'
        DEPARTMENT_STAFF = 'department_staff', 'Department Staff'
        ADMIN = 'admin', 'Administrator'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('email address', unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CITIZEN,
    )
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def is_citizen(self):
        return self.role == self.Role.CITIZEN

    @property
    def is_department_staff(self):
        return self.role == self.Role.DEPARTMENT_STAFF

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN
