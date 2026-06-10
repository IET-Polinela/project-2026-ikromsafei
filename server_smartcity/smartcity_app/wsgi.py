"""
WSGI config for smartcity_project.
"""

import os

from django.core.wsgi import get_wsgi_application

# SUDAH DIUBAH KE smartcity_app [cite: 1241]
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_app.settings')

application = get_wsgi_application()