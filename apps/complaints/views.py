"""
Views for the complaints app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Complaint, ComplaintImage, StatusUpdate
from .forms import ComplaintForm, ComplaintImageForm
from apps.departments.models import Department


def home_view(request):
    """Landing page of the Civic Complaint Management System."""
    return render(request, 'home.html')


@login_required
def submit_complaint_view(request):
    """Handle complaint submission with optional image upload."""
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        image_form = ComplaintImageForm(request.POST, request.FILES)

        if form.is_valid():
            # Save complaint with the logged-in user as complainant
            complaint = form.save(commit=False)
            complaint.complainant = request.user
            complaint.save()

            # Save image if provided
            if image_form.is_valid() and request.FILES.get('image'):
                image = image_form.save(commit=False)
                image.complaint = complaint
                image.save()

            messages.success(
                request,
                f'Complaint submitted successfully! Your tracking ID is: {complaint.tracking_id}'
            )
            return redirect('complaints:detail', tracking_id=complaint.tracking_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintForm()
        image_form = ComplaintImageForm()

    return render(request, 'complaints/submit.html', {
        'form': form,
        'image_form': image_form,
    })


@login_required
def complaint_list_view(request):
    """Show all complaints submitted by the logged-in user."""
    complaints = Complaint.objects.filter(complainant=request.user)

    # Optional status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        complaints = complaints.filter(status=status_filter)

    return render(request, 'complaints/list.html', {
        'complaints': complaints,
        'status_filter': status_filter,
        'status_choices': Complaint.Status.choices,
    })


def complaint_detail_view(request, tracking_id):
    """View details of a specific complaint by its tracking ID."""
    complaint = get_object_or_404(Complaint, tracking_id=tracking_id)
    images = complaint.images.all()
    status_updates = complaint.status_updates.all().order_by('created_at')

    return render(request, 'complaints/detail.html', {
        'complaint': complaint,
        'images': images,
        'status_updates': status_updates,
    })


import json
from django.urls import reverse

def complaint_map_view(request):
    """Show all complaints plotted on a map of Kerala."""
    complaints = Complaint.objects.exclude(
        latitude__isnull=True
    ).exclude(
        longitude__isnull=True
    ).select_related('complainant', 'department')

    complaints_data = []
    for c in complaints:
        complaints_data.append({
            'tracking_id': c.tracking_id,
            'title': c.title,
            'status': c.status,
            'status_display': c.get_status_display(),
            'latitude': float(c.latitude),
            'longitude': float(c.longitude),
            'url': reverse('complaints:detail', kwargs={'tracking_id': c.tracking_id})
        })

    return render(request, 'complaints/map.html', {
        'complaints': complaints,
        'complaints_json': json.dumps(complaints_data),
    })


def is_staff_user(user):
    """Check if user is staff or admin."""
    return user.is_staff or user.role == 'admin'


@login_required
@user_passes_test(is_staff_user, login_url='/')
def admin_dashboard_view(request):
    """Admin dashboard with complaint analytics and management."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # Overall counts
    total = Complaint.objects.count()
    pending = Complaint.objects.filter(status=Complaint.Status.PENDING).count()
    under_review = Complaint.objects.filter(status=Complaint.Status.UNDER_REVIEW).count()
    in_progress = Complaint.objects.filter(status=Complaint.Status.IN_PROGRESS).count()
    resolved = Complaint.objects.filter(status=Complaint.Status.RESOLVED).count()
    rejected = Complaint.objects.filter(status=Complaint.Status.REJECTED).count()

    # Time-based stats
    this_week = Complaint.objects.filter(created_at__gte=seven_days_ago).count()
    this_month = Complaint.objects.filter(created_at__gte=thirty_days_ago).count()

    # Category breakdown (top 8)
    category_stats = (
        Complaint.objects.values('category')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )

    # Priority breakdown
    priority_stats = (
        Complaint.objects.values('priority')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Department workload
    department_stats = (
        Department.objects.filter(is_active=True)
        .annotate(
            total_complaints=Count('complaints'),
            pending_complaints=Count('complaints', filter=Q(complaints__status=Complaint.Status.PENDING)),
            resolved_complaints=Count('complaints', filter=Q(complaints__status=Complaint.Status.RESOLVED)),
        )
        .order_by('-total_complaints')
    )

    # Recent complaints (last 10)
    recent_complaints = (
        Complaint.objects.select_related('complainant', 'department')
        .order_by('-created_at')[:10]
    )

    # Status data for chart (as JSON-safe lists)
    status_labels = ['Pending', 'Under Review', 'In Progress', 'Resolved', 'Rejected']
    status_data = [pending, under_review, in_progress, resolved, rejected]

    context = {
        'total': total,
        'pending': pending,
        'under_review': under_review,
        'in_progress': in_progress,
        'resolved': resolved,
        'rejected': rejected,
        'this_week': this_week,
        'this_month': this_month,
        'resolution_rate': round((resolved / total * 100), 1) if total > 0 else 0,
        'category_stats': category_stats,
        'priority_stats': priority_stats,
        'department_stats': department_stats,
        'recent_complaints': recent_complaints,
        'status_labels': status_labels,
        'status_data': status_data,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)
