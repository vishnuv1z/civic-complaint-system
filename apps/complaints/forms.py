"""
Forms for complaint submission.
"""

from decimal import Decimal

from django import forms
from django.db import models
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
        fields = ('title', 'description', 'category', 'address', 'latitude', 'longitude')
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
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if latitude is None and longitude is None:
            return cleaned_data

        if latitude is None or longitude is None:
            raise forms.ValidationError(
                'Please select a complete location with both latitude and longitude.'
            )

        if not Decimal('-90') <= latitude <= Decimal('90'):
            self.add_error('latitude', 'Latitude must be between -90 and 90.')

        if not Decimal('-180') <= longitude <= Decimal('180'):
            self.add_error('longitude', 'Longitude must be between -180 and 180.')

        return cleaned_data



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


class ComplaintTriageActionForm(forms.Form):
    """Form used by department staff to review, reject, or forward complaints."""

    class Action(models.TextChoices):
        MARK_UNDER_REVIEW = 'under_review', 'Mark Under Review'
        REJECT = 'reject', 'Reject Complaint'
        FORWARD = 'forward', 'Send Complaint to Authority'
        IN_PROGRESS = 'in_progress', 'Mark as In Progress'
        RESOLVED = 'resolved', 'Mark as Resolved'

    action = forms.ChoiceField(
        choices=Action.choices,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 4,
            'placeholder': 'Add triage notes for the timeline or authority email...',
        }),
    )

    def __init__(self, *args, complaint=None, **kwargs):
        super().__init__(*args, **kwargs)
        if complaint and complaint.status in [
            Complaint.Status.FORWARDED,
            Complaint.Status.IN_PROGRESS,
            Complaint.Status.RESOLVED,
            Complaint.Status.REJECTED,
            Complaint.Status.CLOSED,
        ]:
            choices = [c for c in self.fields['action'].choices if c[0] != self.Action.FORWARD]
            self.fields['action'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        remarks = (cleaned_data.get('remarks') or '').strip()

        if action in {self.Action.REJECT, self.Action.FORWARD} and not remarks:
            self.add_error('remarks', 'Remarks are required for this action.')

        return cleaned_data
