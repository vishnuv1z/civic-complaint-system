"""
URL patterns for the accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    path('department/login/', views.DepartmentLoginView.as_view(), name='department_login'),
    path('department/register/', views.department_register_view, name='department_register'),
    path('profile/', views.profile_view, name='profile'),
]
