"""
FASE 1 y 2 · Validación por campo en los formularios y reglas cruzadas en el modelo.
"""
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Libro
from .validators import sanitize_input, validar_nombre


# ---------------------------------------------------------------- ModelForm
class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = ["titulo", "autor", "isbn", "precio", "stock", "publicado"]
        help_texts = {"isbn": "10 o 13 dígitos; se permiten guiones."}

    # --- Nivel 1: validación por campo -------------------------------------
    def clean_titulo(self):
        return sanitize_input(self.cleaned_data["titulo"])

    def clean_autor(self):
        autor = sanitize_input(self.cleaned_data["autor"])
        if len(autor) < 3:
            raise ValidationError("El autor debe tener al menos 3 caracteres.")
        return autor

    def clean_isbn(self):
        isbn = re.sub(r"[-\s]", "", self.cleaned_data["isbn"]).upper()
        qs = Libro.objects.filter(isbn=isbn)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe un libro con este ISBN.")
        return isbn

# ------------------------------------------------------- Formulario clásico
class ContactoForm(forms.Form):
    nombre = forms.CharField(max_length=60, validators=[validar_nombre])
    email = forms.EmailField()
    asunto = forms.CharField(max_length=80)
    mensaje = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), min_length=10, max_length=1000)

    def clean_nombre(self):
        return sanitize_input(self.cleaned_data["nombre"]).title()

    def clean_email(self):
        return sanitize_input(self.cleaned_data["email"], minusculas=True)

    def clean_asunto(self):
        return sanitize_input(self.cleaned_data["asunto"])

    def clean_mensaje(self):
        return sanitize_input(self.cleaned_data["mensaje"])

    def clean(self):
        cleaned = super().clean()
        asunto, mensaje = cleaned.get("asunto"), cleaned.get("mensaje")
        if asunto and mensaje and asunto.lower() == mensaje.lower():
            self.add_error("mensaje", "El mensaje no puede ser igual al asunto.")
        return cleaned


# --------------------------------------------------------------- Registro
class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")   # nunca exponemos is_staff / is_superuser

    def clean_email(self):
        email = sanitize_input(self.cleaned_data["email"], minusculas=True)
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email
