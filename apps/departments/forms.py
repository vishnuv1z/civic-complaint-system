from django import forms
from .models import Department

class DepartmentContactForm(forms.ModelForm):
    """Form for department staff to update their authority contact details."""

    class Meta:
        model = Department
        fields = ('contact_email', 'contact_phone')
        widgets = {
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Authority Email Address'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Authority Phone Number'
            }),
        }
