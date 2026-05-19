"""
Forms for user registration and profile management.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import CustomUser
from apps.departments.models import Department, DepartmentStaff


class CustomUserRegistrationForm(UserCreationForm):
    """Registration form with email as the primary field."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
        })
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name',
        })
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone number',
        })
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')


class DepartmentRegistrationForm(CustomUserRegistrationForm):
    """Registration form for department staff with department selection."""
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-input',
        }),
        empty_label="Select your Department"
    )

    class Meta(CustomUserRegistrationForm.Meta):
        fields = CustomUserRegistrationForm.Meta.fields + ('department',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.DEPARTMENT_STAFF
        if commit:
            user.save()
            DepartmentStaff.objects.create(
                user=user,
                department=self.cleaned_data['department'],
                staff_role=DepartmentStaff.StaffRole.OFFICER
            )
        return user


class CustomLoginForm(AuthenticationForm):
    """Login form using email instead of username."""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
        })
    )


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'phone_number', 'address', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
