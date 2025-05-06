""" Creación de un patrón de URL para las vistas de la creación de empresas.

Para una referencia completa sobre django.urls, consulte
https://docs.djangoproject.com/en/4.0/ref/urls/
"""

from django.urls import path

from .views import ContactAPIView

# Creación de un patrón de URL para las vistas de creación de la empresa.
app_name = "contact"

urlpatterns = [
    # Creación de un patrón de URL para la vista Empresas.
    path("email-django/", ContactAPIView.as_view(), name="contact"),

]   