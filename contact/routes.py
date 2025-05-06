"""
Módulo de rutas de contacto (contact/routes.py)

Este módulo define un conjunto de funciones y un endpoint de FastAPI para:
  - Validar datos de formulario de contacto con Pydantic.
  - Limitar la frecuencia de peticiones (throttling).
  - Enviar correos electrónicos de notificación al administrador.
  - Enviar correos electrónicos de confirmación al remitente.
  - Ejecutar el envío de correos en segundo plano (BackgroundTasks).

Dependencias:
  - Django settings y utilidades de correo.
  - FastAPI para creación de rutas y manejo de tareas en background.
  - Pydantic para validación de entrada.
  - Un limitador de peticiones (configurado en config.throttle).

Uso:
  Montar este router en la aplicación principal de FastAPI:

    from contact.routes import router as contact_router
    app.include_router(contact_router, prefix="/contact")
"""

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from config.throttle import limiter

# Crear un enrutador de FastAPI para las rutas de contacto
router = APIRouter()  # noqa: E305


class Contact(BaseModel):  # pylint: disable=too-few-public-methods
    """
    Modelo de datos de entrada para el endpoint de contacto.

    Atributos:
        name (str): Nombre del remitente.
        apellido (str): Apellido del remitente.
        email (EmailStr): Correo electrónico válido.
        phone (str): Número de teléfono de contacto.
        message (str): Mensaje de texto enviado por el remitente.
    """
    name: str
    apellido: str
    email: EmailStr
    phone: str
    message: str


def envio_email(subject: str, body: str, recipients: list[str], html: bool = False) -> None:
    """
    Envía un correo electrónico, ya sea en formato texto o HTML.

    Args:
        subject (str): Asunto del correo.
        body (str): Cuerpo del correo (texto plano o HTML).
        recipients (list[str]): Lista de direcciones de correo destino.
        html (bool): Si es True, envía el cuerpo como HTML. Por defecto False.

    Lanza:
        Excepción si falla el envío (fail_silently=False).
    """
    if html:
        # Construir EmailMessage para contenido HTML
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.content_subtype = 'html'  # Indicar que el cuerpo es HTML
        email.send(fail_silently=False)
    else:
        # Envío de texto plano con send_mail
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )


def info_admin(name: str, apellido: str, email: str, phone: str, message: str) -> None:
    """
    Prepara y envía un correo al administrador con los datos del contacto.

    Args:
        name (str): Nombre del remitente.
        apellido (str): Apellido del remitente.
        email (str): Correo del remitente.
        phone (str): Teléfono del remitente.
        message (str): Mensaje enviado por el remitente.
    """
    subject = "Nuevo mensaje de contacto"
    body = (
        f"Nombre: {name} {apellido}\n"
        f"Email: {email}\n"
        f"Teléfono: {phone}\n\n"
        f"Mensaje:\n{message}"
    )
    # Enviar al correo por defecto configurado en Django
    envio_email(subject, body, [settings.DEFAULT_FROM_EMAIL])


def info_remitente(name: str, apellido: str, recipient_email: str) -> None:
    """
    Envía un correo de confirmación al remitente del mensaje.

    Args:
        name (str): Nombre del remitente.
        apellido (str): Apellido del remitente.
        recipient_email (str): Correo del remitente para enviar la confirmación.
    """
    subject = "Confirmación de recepción de mensaje"
    # Renderizar plantilla HTML con los datos del remitente
    html_body = render_to_string(
        "confirmation_email.html",
        {"name": name, "apellido": apellido}
    )
    envio_email(subject, html_body, [recipient_email], html=True)


@router.post("/", status_code=201)
@limiter.limit("1/minute")  # ≤ 1 petición por minuto por IP o usuario
async def contact(
    request: Request,
    contact: Contact,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Endpoint POST para procesar formularios de contacto.

    - Valida los datos de entrada usando Pydantic (Contact).
    - Aplica un límite de 1 petición por minuto por IP/usuario.
    - Envía los correos en segundo plano para no bloquear la respuesta.

    Args:
        request (Request): Objeto de petición (no utilizado directamente).
        contact (Contact): Datos validados del formulario de contacto.
        background_tasks (BackgroundTasks): Manager para tareas en background.

    Returns:
        JSONResponse: Mensaje de éxito si el envío se programa correctamente.
    """
    # Programar envío de correo al administrador
    background_tasks.add_task(
        info_admin,
        contact.name,
        contact.apellido,
        contact.email,
        contact.phone,
        contact.message
    )
    # Programar envío de correo de confirmación al remitente
    background_tasks.add_task(
        info_remitente,
        contact.name,
        contact.apellido,
        contact.email
    )

    return JSONResponse(
        {"message": "Correo(s) enviado(s) con éxito"},
        status_code=201
    )
