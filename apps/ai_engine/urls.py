from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('generate-description/', views.generate_description_view, name='generate_description'),
    path('rewrite-title/', views.rewrite_title_view, name='rewrite_title'),
    path('categorize/', views.categorize_complaint_view, name='categorize'),
]
