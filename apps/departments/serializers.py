"""
REST API serializers for the departments app.
"""

from rest_framework import serializers
from .models import Department, DepartmentStaff


class DepartmentSerializer(serializers.ModelSerializer):
    complaint_count = serializers.IntegerField(source='complaints.count', read_only=True)
    staff_count = serializers.IntegerField(source='staff_members.count', read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description',
            'head_name', 'contact_email', 'contact_phone',
            'categories', 'is_active',
            'complaint_count', 'staff_count',
        ]


class DepartmentStaffSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = DepartmentStaff
        fields = ['id', 'user', 'user_name', 'department', 'department_name', 'staff_role', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']
