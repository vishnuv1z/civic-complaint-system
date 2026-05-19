"""
Views for the departments app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .forms import DepartmentContactForm

def is_department_staff(user):
    return user.is_authenticated and user.role == 'department_staff' and hasattr(user, 'department_assignment')

@login_required
@user_passes_test(is_department_staff, login_url='/')
def department_settings_view(request):
    """View for department staff to update their department's contact info."""
    department = request.user.department_assignment.department

    if request.method == 'POST':
        form = DepartmentContactForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department contact details updated successfully.')
            return redirect('departments:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DepartmentContactForm(instance=department)

    return render(request, 'departments/settings.html', {
        'form': form,
        'department': department
    })
