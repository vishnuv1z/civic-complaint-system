"""
Admin configuration for the notifications app.
"""

from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient', 'channel', 'status', 'sent_at', 'created_at')
    list_filter = ('channel', 'status', 'created_at')
    search_fields = ('subject', 'recipient__email')
    readonly_fields = ('created_at',)
