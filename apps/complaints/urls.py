"""
URL patterns for the complaints app.
"""

from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.home_view, name='home'),
]
