"""
Views for the complaints app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from .models import Complaint
from .forms import ComplaintForm, ComplaintImageForm, ComplaintTriageActionForm
from apps.departments.models import Department
from services.complaint_service import (
    create_complaint,
    forward_complaint_to_authority,
    update_complaint_status,
)


def home_view(request):
    """Landing page of the Civic Complaint Management System."""
    return render(request, 'home.html')


@login_required
def submit_complaint_view(request):
    """Handle complaint submission with optional image upload."""
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        image_form = ComplaintImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            complaint = create_complaint(
                complainant=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                category=form.cleaned_data.get('category'),
                address=form.cleaned_data.get('address'),
                latitude=form.cleaned_data.get('latitude'),
                longitude=form.cleaned_data.get('longitude'),
                image_file=image_form.cleaned_data.get('image'),
                image_caption=image_form.cleaned_data.get('caption'),
            )

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

def _coordinate_to_float(value):
    """Return a JavaScript-safe coordinate number, or None when unavailable."""
    if value in (None, ''):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_valid_coordinate_pair(latitude, longitude):
    return (
        latitude is not None
        and longitude is not None
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def _complaints_map_payload(complaints):
    """Serialize complaint location data for templates and the JSON endpoint."""
    payload = []

    for complaint in complaints:
        latitude = _coordinate_to_float(complaint.latitude)
        longitude = _coordinate_to_float(complaint.longitude)

        payload.append({
            'tracking_id': complaint.tracking_id,
            'title': complaint.title,
            'status': complaint.status,
            'status_display': complaint.get_status_display(),
            'latitude': latitude,
            'longitude': longitude,
            'has_valid_coordinates': _is_valid_coordinate_pair(latitude, longitude),
            'url': reverse('complaints:detail', kwargs={'tracking_id': complaint.tracking_id}),
        })

    return payload


def complaint_coordinates_api(request):
    """Return complaint coordinates for Leaflet marker rendering."""
    complaints = Complaint.objects.only(
        'tracking_id',
        'title',
        'status',
        'latitude',
        'longitude',
    ).order_by('-created_at')
    complaints_data = _complaints_map_payload(complaints)

    return JsonResponse({
        'count': len(complaints_data),
        'mapped_count': sum(1 for c in complaints_data if c['has_valid_coordinates']),
        'complaints': complaints_data,
    })


def public_complaints_view(request):
    """Show a gallery of all public complaints and a map."""
    complaints = Complaint.objects.select_related('complainant').prefetch_related('images').order_by('-created_at')
    complaints_data = _complaints_map_payload(complaints)

    return render(request, 'complaints/public_list.html', {
        'complaints': complaints,
        'complaints_json': complaints_data,
        'mapped_count': sum(1 for c in complaints_data if c['has_valid_coordinates']),
    })


def complaint_map_view(request):
    """Show a dedicated public map of complaint locations."""
    complaints = Complaint.objects.order_by('-created_at')
    complaints_data = _complaints_map_payload(complaints)

    return render(request, 'complaints/map.html', {
        'complaints': complaints,
        'complaints_json': complaints_data,
        'mapped_count': sum(1 for c in complaints_data if c['has_valid_coordinates']),
    })


def can_manage_department_complaints(user):
    """Allow admins/staff and assigned department users into the triage UI."""
    if not user.is_authenticated:
        return False

    if user.is_staff or getattr(user, 'role', '') == 'admin':
        return True

    if getattr(user, 'role', '') == 'department_staff':
        return hasattr(user, 'department_assignment')

    return False


def _manageable_complaints_for(user):
    complaints = Complaint.objects.select_related(
        'complainant',
        'department',
    ).prefetch_related('images')

    if user.is_staff or getattr(user, 'role', '') == 'admin':
        return complaints

    try:
        return complaints.filter(department=user.department_assignment.department)
    except Exception:
        return complaints.none()


@login_required
@user_passes_test(can_manage_department_complaints, login_url='/')
def department_complaint_queue_view(request):
    """Department triage queue for reviewing complaints before forwarding."""
    complaints = _manageable_complaints_for(request.user)

    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')

    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter)
    if category_filter:
        complaints = complaints.filter(category=category_filter)

    base_queryset = _manageable_complaints_for(request.user)
    categories = (
        base_queryset.exclude(category__isnull=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    context = {
        'complaints': complaints.order_by('-created_at'),
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'status_choices': Complaint.Status.choices,
        'priority_choices': Complaint.Priority.choices,
        'categories': categories,
        'pending_count': base_queryset.filter(status=Complaint.Status.PENDING).count(),
        'review_count': base_queryset.filter(status=Complaint.Status.UNDER_REVIEW).count(),
        'forwarded_count': base_queryset.filter(status=Complaint.Status.FORWARDED).count(),
        'in_progress_count': base_queryset.filter(status=Complaint.Status.IN_PROGRESS).count(),
        'resolved_count': base_queryset.filter(status=Complaint.Status.RESOLVED).count(),
        'rejected_count': base_queryset.filter(status=Complaint.Status.REJECTED).count(),
        'complaints_json': _complaints_map_payload(complaints),
    }

    return render(request, 'complaints/staff_queue.html', context)


@login_required
@user_passes_test(can_manage_department_complaints, login_url='/')
def department_complaint_review_view(request, tracking_id):
    """Review one complaint and either mark, reject, or forward it."""
    complaint = get_object_or_404(
        _manageable_complaints_for(request.user).prefetch_related(
            'status_updates',
            'forward_logs',
        ),
        tracking_id=tracking_id,
    )

    if request.method == 'POST':
        form = ComplaintTriageActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            remarks = form.cleaned_data.get('remarks', '')

            try:
                if action == ComplaintTriageActionForm.Action.MARK_UNDER_REVIEW:
                    update_complaint_status(
                        complaint=complaint,
                        new_status=Complaint.Status.UNDER_REVIEW,
                        changed_by=request.user,
                        remarks=remarks or 'Marked under review by department staff.',
                    )
                    messages.success(request, 'Complaint marked under review.')
                elif action == ComplaintTriageActionForm.Action.REJECT:
                    update_complaint_status(
                        complaint=complaint,
                        new_status=Complaint.Status.REJECTED,
                        changed_by=request.user,
                        remarks=remarks,
                    )
                    messages.success(request, 'Complaint rejected and logged.')
                elif action == ComplaintTriageActionForm.Action.FORWARD:
                    forward_complaint_to_authority(
                        complaint=complaint,
                        forwarded_by=request.user,
                        remarks=remarks,
                    )
                    messages.success(request, 'Complaint sent to the official authority contact.')
                elif action == ComplaintTriageActionForm.Action.IN_PROGRESS:
                    update_complaint_status(
                        complaint=complaint,
                        new_status=Complaint.Status.IN_PROGRESS,
                        changed_by=request.user,
                        remarks=remarks or 'Marked in progress by department staff.',
                    )
                    messages.success(request, 'Complaint marked as in progress.')
                elif action == ComplaintTriageActionForm.Action.RESOLVED:
                    update_complaint_status(
                        complaint=complaint,
                        new_status=Complaint.Status.RESOLVED,
                        changed_by=request.user,
                        remarks=remarks or 'Marked resolved by department staff.',
                    )
                    messages.success(request, 'Complaint marked as resolved.')
            except Exception as exc:
                messages.error(request, f'Unable to complete action: {exc}')

            return redirect('complaints:staff_review', tracking_id=complaint.tracking_id)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintTriageActionForm()

    return render(request, 'complaints/staff_review.html', {
        'complaint': complaint,
        'images': complaint.images.all(),
        'status_updates': complaint.status_updates.all().order_by('created_at'),
        'forward_logs': complaint.forward_logs.all(),
        'form': form,
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
    forwarded = Complaint.objects.filter(status=Complaint.Status.FORWARDED).count()
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
    status_labels = ['Pending', 'Under Review', 'Forwarded', 'In Progress', 'Resolved', 'Rejected']
    status_data = [pending, under_review, forwarded, in_progress, resolved, rejected]

    context = {
        'total': total,
        'pending': pending,
        'under_review': under_review,
        'in_progress': in_progress,
        'forwarded': forwarded,
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
