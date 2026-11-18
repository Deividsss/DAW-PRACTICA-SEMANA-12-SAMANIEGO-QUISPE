"""Validadores reutilizables (Fase 2 · nivel campo)."""
import re
from django.core.validators import RegexValidator
from django.utils.html import strip_tags

# Solo letras (con tildes), espacios, apóstrofes y guiones
validar_nombre = RegexValidator(
    regex=r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' -]{2,60}$",
    message="Usa solo letras y espacios (2 a 60 caracteres).",
    code="nombre_invalido",
)

# ISBN: 10 o 13 dígitos (se aceptan guiones y se limpian en clean_isbn)
validar_isbn = RegexValidator(
    regex=r"^(?:\d[- ]?){9}[\dXx]$|^(?:\d[- ]?){12}\d$",
    message="ISBN inválido. Debe tener 10 o 13 dígitos.",
    code="isbn_invalido",
)


def sanitize_input(texto: str, *, minusculas: bool = False) -> str:
    """Sanitización básica ANTES de persistir.

    - strip_tags: elimina etiquetas HTML (previene XSS almacenado).
    - strip(): quita espacios laterales.
    - colapsa espacios repetidos.
    - lower(): opcional (emails, usernames).
    El escape de salida lo hace el motor de plantillas (autoescape), y el ORM
    parametriza las consultas, lo que previene SQLi.
    """
    texto = strip_tags(texto or "")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.lower() if minusculas else texto
