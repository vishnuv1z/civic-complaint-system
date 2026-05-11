"""
Forms for complaint submission.
"""

from django import forms
from .models import Complaint, ComplaintImage


class ComplaintForm(forms.ModelForm):
    """Form for citizens to submit a new complaint."""

    class Meta:
        model = Complaint
        fields = ('title', 'description', 'category', 'address')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Brief title of your complaint',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Describe the issue in detail...',
                'rows': 5,
            }),
            'category': forms.Select(attrs={
                'class': 'form-input',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Location / address of the issue',
                'rows': 2,
            }),
        }


class ComplaintImageForm(forms.ModelForm):
    """Form for uploading images with a complaint."""

    class Meta:
        model = ComplaintImage
        fields = ('image', 'caption')
        widgets = {
            'caption': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optional caption',
            }),
        }
