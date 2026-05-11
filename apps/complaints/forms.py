"""
Forms for complaint submission.
"""

from django import forms
from .models import Complaint, ComplaintImage


# Category choices for the complaint form
CATEGORY_CHOICES = [
    ('', 'Select a category'),
    ('Road & Pothole', 'Road & Pothole'),
    ('Water Supply', 'Water Supply'),
    ('Drainage & Sewage', 'Drainage & Sewage'),
    ('Electricity', 'Electricity'),
    ('Garbage & Sanitation', 'Garbage & Sanitation'),
    ('Street Light', 'Street Light'),
    ('Public Transport', 'Public Transport'),
    ('Noise Pollution', 'Noise Pollution'),
    ('Illegal Construction', 'Illegal Construction'),
    ('Park & Playground', 'Park & Playground'),
    ('Traffic Signal', 'Traffic Signal'),
    ('Public Safety', 'Public Safety'),
    ('Other', 'Other'),
]


class ComplaintForm(forms.ModelForm):
    """Form for citizens to submit a new complaint."""

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-input',
        }),
    )

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
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Location / address of the issue',
                'rows': 2,
            }),
        }


class ComplaintImageForm(forms.ModelForm):
    """Form for uploading images with a complaint."""

    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-input',
            'accept': 'image/*',
        }),
    )

    class Meta:
        model = ComplaintImage
        fields = ('image', 'caption')
        widgets = {
            'caption': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optional caption for the image',
            }),
        }
