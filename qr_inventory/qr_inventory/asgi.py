"""
ASGI config for qr_inventory project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qr_inventory.settings')

application = get_asgi_application() 