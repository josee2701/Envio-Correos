# config/asgi.py

import os
from pathlib import Path

from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config.throttle import limiter
from contact.routes import router as contact_router

# 1) Configuración Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
BASE_DIR = Path(__file__).resolve().parent.parent

# 2) ASGI de Django
django_asgi_app = get_asgi_application()

# 3) FastAPI principal
app = FastAPI()

# Orígenes que permites
origins = [
    "https://josee2701.github.io",
    "https://jose-campos.netlify.app"
]

# ————————————————————————————
# REDIRECCIONES
# 4a) Raíz “/” → /web/admin/
@app.get("/", include_in_schema=False)
async def redirect_root():
    return RedirectResponse(url="/web/api-auth/login/", status_code=302)

# 4b) “/web” y “/web/” → /web/admin/
@app.get("/web", include_in_schema=False)
@app.get("/web/", include_in_schema=False)
async def redirect_web():
    return RedirectResponse(url="/web/api-auth/login/", status_code=302)
# ————————————————————————————

# 5) Middleware y handler de SlowAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          
    allow_credentials=True,          
    allow_methods=["*"],             
    allow_headers=["*"],              
)


# 6) Montaje de estáticos y aplicación Django bajo /web
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "staticfiles")), name="static")
app.mount("/web", django_asgi_app)

# 7) Rutas de tu API de contacto
app.include_router(contact_router, prefix="/api/contact", tags=["contact"])

# 8) Exportamos ASGI
application = app
