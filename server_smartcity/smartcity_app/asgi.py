"""
ASGI config for smartcity_project.
"""

import os

from django.core.asgi import get_asgi_application

# SUDAH DIUBAH KE smartcity_app
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_app.settings')

application = get_asgi_application()