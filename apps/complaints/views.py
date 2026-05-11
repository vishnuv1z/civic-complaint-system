"""
Views for the complaints app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Complaint, ComplaintImage
from .forms import ComplaintForm, ComplaintImageForm


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


def complaint_map_view(request):
    """Show all complaints plotted on a map of Kerala."""
    complaints = Complaint.objects.exclude(
        latitude__isnull=True
    ).exclude(
        longitude__isnull=True
    ).select_related('complainant', 'department')

    return render(request, 'complaints/map.html', {
        'complaints': complaints,
    })

