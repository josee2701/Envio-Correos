from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

# Datos correctos: aquí ponemos todo lo que pide la API
valid_data = {
    "name": "John",
    "apellido": "Doe",
    "email": "jose.campos.tecni@gmail.com",
    "phone": 312323232,
    "message": "Hello, this is a test message."
}

# Datos incorrectos: le falta el campo "email"
invalid_data = {
    "name": "John",
    "apellido": "Doe",
    "phone": 312323232,
    "message": "Missing email!"
}

class ContactAPIViewTests(TestCase):
    # Este método se llama antes de cada test para preparar todo
    def setUp(self):
        # Creamos un cliente que simula peticiones HTTP
        self.client = APIClient()
        self.url = reverse('contact:contact')

    @patch('contact.views.ContactAPIView.envio_email')
    def test_contact_success_calls_envio_email(self, mock_envio):
        """
        1) Enviamos datos válidos.
        2) Debe responder 201 (Creado).
        3) Debe llamar dos veces al método envio_email.
        """
        # Hacemos un POST a la URL con valid_data
        response = self.client.post(self.url, valid_data, format='json')

        # 1) Verificamos que la respuesta sea 201
        self.assertEqual(response.status_code, 201)

        # 2) Verificamos que el JSON tenga el mensaje esperado
        self.assertEqual(
            response.data,
            {'message': 'Correo(s) enviado(s) con éxito'}
        )

        # 3) Comprobamos que envio_email se llamó dos veces
        self.assertEqual(mock_envio.call_count, 2)

    # ———————————————————————————————————————————————
    def test_contact_invalid_data_returns_400(self):
        """
        1) Enviamos datos que faltan información (sin email).
        2) Debe responder 400 (Solicitud incorrecta).
        3) Debe decirnos que falta el campo 'email'.
        """
        response = self.client.post(self.url, invalid_data, format='json')
        # 1) Y 2): código 400
        self.assertEqual(response.status_code, 400)
        # 3): el diccionario de errores debe incluir "email"
        self.assertIn('email', response.data)

    @patch('contact.views.ContactAPIView.envio_email',side_effect=Exception('SMTP down'))
    def test_contact_email_exception_returns_500(self, mock_envio):
        """
        1) Forzamos que envio_email lance un error.
        2) Así la vista debe responder 500 (Error interno).
        3) Debe venir un mensaje que empiece con "Error al enviar correo".
        """
        response = self.client.post(self.url, valid_data, format='json')
        # 1) y 2): código 500
        self.assertEqual(response.status_code, 500)
        # 3): comprobamos que venga la clave "error"
        self.assertIn('error', response.data)
        # Y que el texto empiece como esperamos
        self.assertTrue(
            response.data['error'].startswith('Error al enviar correo')
        )
