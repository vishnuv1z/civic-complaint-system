"""
Views for the departments app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from urllib.parse import urlencode

from .forms import DepartmentContactForm

def is_department_staff(user):
    return user.is_authenticated and user.role == 'department_staff' and hasattr(user, 'department_assignment')

@login_required
@user_passes_test(is_department_staff, login_url='/')
def department_settings_view(request):
    """View for department staff to update their department's contact info."""
    department = request.user.department_assignment.department
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = DepartmentContactForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department contact details updated successfully. Redirecting shortly...')
            if next_url:
                url = reverse('departments:settings')
                params = urlencode({'next': next_url, 'success': '1'})
                return HttpResponseRedirect(f"{url}?{params}")
            return redirect('departments:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DepartmentContactForm(instance=department)

    return render(request, 'departments/settings.html', {
        'form': form,
        'department': department,
        'next_url': next_url
    })
