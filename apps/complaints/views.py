"""
Views for the complaints app.
"""

from django.shortcuts import render


def home_view(request):
    """Landing page of the Civic Complaint Management System."""
    return render(request, 'home.html')
