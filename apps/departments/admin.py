"""
Admin configuration for the departments app.
"""

from django.contrib import admin
from .models import Department, DepartmentStaff


class DepartmentStaffInline(admin.TabularInline):
    model = DepartmentStaff
    extra = 0


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head_name', 'contact_email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'head_name')
    inlines = [DepartmentStaffInline]


@admin.register(DepartmentStaff)
class DepartmentStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'staff_role', 'assigned_at')
    list_filter = ('staff_role', 'department')
