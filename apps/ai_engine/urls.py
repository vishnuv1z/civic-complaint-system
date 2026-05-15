from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('generate-description/', views.generate_description_view, name='generate_description'),
]
