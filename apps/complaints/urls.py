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
    path('complaints/track/', views.track_complaint_view, name='track'),
    path('complaints/coordinates/', views.complaint_coordinates_api, name='coordinates_api'),
    path('complaints/coordinates/department/', views.department_complaint_coordinates_api, name='department_coordinates_api'),
    path('complaints/map/', views.complaint_map_view, name='map'),
    path('complaints/staff/', views.department_complaint_queue_view, name='staff_queue'),
    path('complaints/staff/<str:tracking_id>/', views.department_complaint_review_view, name='staff_review'),
    path('complaints/', views.complaint_list_view, name='list'),
    path('complaints/explore/', views.public_complaints_view, name='explore'),
    path('complaints/<str:tracking_id>/', views.complaint_detail_view, name='detail'),
]
