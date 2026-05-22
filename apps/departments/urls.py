"""
URL patterns for the departments app.
"""

from django.urls import path

app_name = 'departments'

from . import views

urlpatterns = [
    path('settings/', views.department_settings_view, name='settings'),
]
