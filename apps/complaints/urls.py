"""
URL patterns for the complaints app.
"""

from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.admin_dashboard_view, name='dashboard'),
    path('complaints/submit/', views.submit_complaint_view, name='submit'),
    path('complaints/', views.complaint_list_view, name='list'),
    path('complaints/map/', views.complaint_map_view, name='map'),
    path('complaints/<str:tracking_id>/', views.complaint_detail_view, name='detail'),
]
