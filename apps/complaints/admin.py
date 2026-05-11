"""
Admin configuration for the complaints app.
"""

from django.contrib import admin
from .models import Complaint, ComplaintImage, StatusUpdate


class ComplaintImageInline(admin.TabularInline):
    model = ComplaintImage
    extra = 0
    readonly_fields = ('uploaded_at',)


class StatusUpdateInline(admin.TabularInline):
    model = StatusUpdate
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'created_at')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_id', 'title', 'complainant', 'category',
        'status', 'priority', 'department', 'created_at',
    )
    list_filter = ('status', 'priority', 'category', 'department', 'created_at')
    search_fields = ('tracking_id', 'title', 'description', 'complainant__email')
    readonly_fields = ('id', 'tracking_id', 'ai_category', 'ai_confidence', 'created_at', 'updated_at')
    inlines = [ComplaintImageInline, StatusUpdateInline]

    fieldsets = (
        ('Basic Info', {'fields': ('id', 'tracking_id', 'complainant', 'title', 'description')}),
        ('Classification', {'fields': ('category', 'ai_category', 'ai_confidence', 'department')}),
        ('Status', {'fields': ('status', 'priority')}),
        ('Location', {'fields': ('address', 'latitude', 'longitude')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'resolved_at')}),
    )


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status', 'created_at')
    readonly_fields = ('created_at',)
