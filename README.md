# Proyecto “Envío de Correos” con Django, DRF y FastAPI

Una pequeña aplicación que une **Django** (con Django REST Framework) y **FastAPI** en un solo servidor ASGI para:

* **Django**: Panel de administración, autenticación, estáticos, etc.
* **DRF**: Vista `ContactAPIView` para envío de correos.
* **FastAPI**: Endpoint `/api/contact/` con validación Pydantic, *throttling* y tareas en background.

---

## 📁 Estructura de directorios

```
.
├── config/  
│   ├── __init__.py  
│   ├── asgi.py          ← Integración ASGI (Django + FastAPI)  
│   ├── settings.py
│   ├── throttle.py      ← Configuración de límite de peticiones  
│   ├── urls.py
│   └── wsgi.py
├── contact/  
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── routes.py       ← Router de FastAPI  
│   ├── serializers.py  ← Serializador DRF  
│   ├── tests.py
│   ├── urls.py         ← Rutas DRF (opcional)  
│   └── views.py        ← `ContactAPIView` de DRF  
├── staticfiles/        ← Archivos estáticos compilados  
├── venv/
├── .gitignore
├── db.sqlite3
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── README.md           ← ESTE ARCHIVO
└── requirements.txt
```

---

## 🛠️ Tecnologías

* **Python 3.10+**
* **Django 4.x**
* **Django REST Framework**
* **FastAPI**
* **Uvicorn** o **Daphne**
* **slowapi** para *rate-limiting*
* **asgiref** para puente sync/async
* **BackgroundTasks** de FastAPI / `asyncio.create_task` en DRF
* **SQLite** (por defecto)

---

## 🚀 Instalación y ejecución

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/tu-organizacion/envio-correos.git
   cd envio-correos
   ```

2. **Crear entorno virtual e instalar dependencias**

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   Define en tu `.env` o entorno:

   ```
   DJANGO_SETTINGS_MODULE=config.settings
   DEFAULT_FROM_EMAIL=tu@email.com
   EMAIL_HOST=…
   EMAIL_PORT=…
   EMAIL_HOST_USER=…
   EMAIL_HOST_PASSWORD=…
   EMAIL_USE_TLS=True
   ```

4. **Migraciones y estáticos**

   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

5. **Levantar en desarrollo**
   Con **Uvicorn**:

   ```bash
   uvicorn config.asgi:application --reload
   ```

   O con **Daphne**:

   ```bash
   daphne -b 0.0.0.0 -p 8000 config.asgi:application
   ```

   También con Docker Compose:

   ```bash
   docker-compose up --build
   ```

---

## 🔗 Punto de entrada ASGI

```python
# config/asgi.py
import os
from pathlib import Path
from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Orígenes permitidos
origins = [
    "https://josee2701.github.io",
    "https://jose-campos.netlify.app"
]

# — Redirecciones básicas —
@app.get("/", include_in_schema=False)
async def redirect_root():
    return RedirectResponse(url="/web/api-auth/login/", status_code=302)

@app.get("/web", include_in_schema=False)
@app.get("/web/", include_in_schema=False)
async def redirect_web():
    return RedirectResponse(url="/web/api-auth/login/", status_code=302)

# 5) Throttling con SlowAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 6) CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 7) Estáticos y montaje de Django en /web
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "staticfiles")), name="static")
app.mount("/web", django_asgi_app)

# 8) Router de FastAPI para contacto
app.include_router(contact_router, prefix="/api/contact", tags=["contact"])

# 9) Exportar aplicación ASGI
application = app
```

---

## 📨 Endpoints de Contacto

### DRF – `ContactAPIView`

* **URL**: `/web/api/contact/`
* **Método**: `POST`
* **Flujo**:

  1. Valida con `ContactSerializer`.
  2. Envía correo al admin con `asyncio.create_task`.
  3. Envía confirmación HTML al remitente.

### FastAPI – `contact_router`

* **URL**: `/api/contact/`
* **Método**: `POST`
* **Throttle**: 1 petición/minuto
* **Validación**: Pydantic `Contact`
* **BackgroundTasks**:

  ```python
  @router.post("/", status_code=201)
  @limiter.limit("1/minute")
  async def contact(..., background_tasks: BackgroundTasks):
      background_tasks.add_task(info_admin, …)
      background_tasks.add_task(info_remitente, …)
      return JSONResponse({"message": "Correo(s) enviado(s) con éxito"}, 201)
  ```

---

## 📝 Personalización

* Ajusta **URLs**, **CORS**, **límite de peticiones** o **plantillas** según tu proyecto.
* Agrega rutas o serializadores en `contact/` si lo requieres.

---

## 📜 Licencia

MIT © 2025
