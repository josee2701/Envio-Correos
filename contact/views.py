from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ContactSerializer


class ContactAPIView(APIView):
    """
    Esta clase atiende peticiones POST para enviar correos.
    No requiere usuario autenticado (AllowAny).
    """

    permission_classes = [AllowAny]  # Cualquiera puede usar esta vista

    def post(self, request, *args, **kwargs):
        """
        Método que se ejecuta cuando alguien hace POST.
        1) Valida datos.
        2) Envía correo al admin.
        3) Envía confirmación al remitente.
        4) Devuelve éxito o error.
        """
        # 1) Creamos el "serializador" y le damos los datos enviados
        serializer = ContactSerializer(data=request.data)

        # 2) Si los datos NO son válidos, devolvemos errores y código 400
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 3) Si son válidos, los guardamos en "data"
        data = serializer.validated_data

        try:
            # 4) Enviamos primer correo al admin
            self.info_admin(
                data['name'],
                data['apellido'],
                data['email'],
                data['phone'],
                data['message'],
            )
            # 5) Enviamos segundo correo de confirmación al remitente
            self.info_remitente(
                data['name'],
                data['apellido'],
                data['email'],
            )
        except Exception as e:
            # 6) Si algo falla al enviar cualquiera de los correos, devolvemos error 500
            return Response(
                {'error': f'Error al enviar correo: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 7) Si todo fue bien, devolvemos mensaje de éxito con código 201
        return Response(
            {'message': 'Correo(s) enviado(s) con éxito'},
            status=status.HTTP_201_CREATED
        )

    def envio_email(self, subject: str, body: str, recipients: list[str], html: bool = False) -> None:
        """
        Envía un correo:
        - Si html=True, arma un EmailMessage con cuerpo HTML.
        - Si html=False, usa send_mail (texto plano).
        Lanza excepción si falla.
        """
        if html:
            # 1) Creamos un correo HTML
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.content_subtype = 'html'     # Decimos que el contenido es HTML
            email.send(fail_silently=False)    # Enviamos y avisamos si hay error
        else:
            # 2) Correo de texto plano
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False,           # Enviamos y avisamos si hay error
            )

    def info_admin(self, name: str, apellido: str, email: str, phone: str, message: str) -> None:
        """
        Prepara y envía un correo de aviso al administrador
        con todos los datos del formulario.
        """
        subject = 'Nuevo mensaje de contacto'
        body = (
            f"Nombre: {name} {apellido}\n"
            f"Email: {email}\n"
            f"Teléfono: {phone}\n\n"
            f"Mensaje:\n{message}"
        )
        # Usamos envio_email para mandarlo
        self.envio_email(subject, body, [settings.DEFAULT_FROM_EMAIL])

    def info_remitente(self, name: str, apellido: str, recipient_email: str) -> None:
        """
        Prepara y envía una confirmación al usuario que escribió,
        usando una plantilla HTML.
        """
        subject = 'Confirmación de recepción de mensaje'
        # Renderizamos la plantilla HTML con el nombre y apellido
        html_body = render_to_string(
            'confirmation_email.html',
            {'name': name, 'apellido': apellido}
        )
        # Mandamos el correo HTML
        self.envio_email(subject, html_body, [recipient_email], html=True)
