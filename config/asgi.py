"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from typing import Union

from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config.settings import BASE_DIR

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()

# 2) App de FastAPI
app = FastAPI(title="API de alto rendimiento")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "staticfiles")), name="static")

# 3) Montar Django bajo una ruta, por ejemplo '/web'
app.mount("/web", application)