"""
Django settings package.
Automatically loads the correct settings module based on the DJANGO_ENV
environment variable. Defaults to 'development' if not set.
"""
import os

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
