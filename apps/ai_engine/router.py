"""
Auto-routing logic for complaints.

Routes classified complaints to the appropriate government department
based on the AI-assigned category.

Will be fully implemented in Phase 9.
"""

from apps.departments.models import Department


def route_complaint(category: str) -> Department | None:
    """
    Find the appropriate department for a given complaint category.

    Args:
        category: The complaint category (from AI classifier or manual selection).

    Returns:
        Department instance or None if no match found.
    """
    if not category:
        return None

    try:
        # Works well on PostgreSQL JSONField.
        department = Department.objects.filter(
            categories__contains=[category],
            is_active=True,
        ).first()
        if department:
            return department
    except Exception:
        # SQLite does not support every JSON containment lookup Django exposes.
        pass

    for department in Department.objects.filter(is_active=True):
        if category in (department.categories or []):
            return department

    return None
