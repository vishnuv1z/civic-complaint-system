"""
REST API serializers for the complaints app.
"""

from rest_framework import serializers
from .models import Complaint, ComplaintImage, StatusUpdate


class ComplaintImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintImage
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class StatusUpdateSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = StatusUpdate
        fields = ['id', 'old_status', 'new_status', 'changed_by_name', 'remarks', 'created_at']
        read_only_fields = ['id', 'created_at']


class ComplaintSerializer(serializers.ModelSerializer):
    images = ComplaintImageSerializer(many=True, read_only=True)
    status_updates = StatusUpdateSerializer(many=True, read_only=True)
    complainant_name = serializers.CharField(source='complainant.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)

    class Meta:
        model = Complaint
        fields = [
            'id', 'tracking_id', 'complainant_name', 'title', 'description',
            'category', 'ai_category', 'ai_confidence',
            'department', 'department_name',
            'status', 'priority',
            'address', 'latitude', 'longitude',
            'images', 'status_updates',
            'created_at', 'updated_at', 'resolved_at',
        ]
        read_only_fields = [
            'id', 'tracking_id', 'ai_category', 'ai_confidence',
            'created_at', 'updated_at', 'resolved_at',
        ]


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new complaint via API."""

    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'address', 'latitude', 'longitude']
