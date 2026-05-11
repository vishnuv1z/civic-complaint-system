"""
Root URL configuration for the Civic Complaint Management System.

Routes:
    /              — Home page
    /admin/        — Django admin
    /accounts/     — Authentication (login, register, profile)
    /complaints/   — Complaint submission & tracking
    /departments/  — Department views
    /api/          — REST API endpoints
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('apps.complaints.urls', namespace='complaints')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('departments/', include('apps.departments.urls', namespace='departments')),

    # REST API (will be expanded in Phase 6)
    # path('api/', include('apps.complaints.api_urls', namespace='api-complaints')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar
    try:
        import debug_toolbar  # noqa: F401
        urlpatterns = [
            path('__debug__/', include('debug_toolbar.urls')),
        ] + urlpatterns
    except ImportError:
        pass