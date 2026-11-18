from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from .validators import validar_isbn


class Libro(models.Model):
    titulo = models.CharField("Título", max_length=150)
    autor = models.CharField(max_length=100)
    isbn = models.CharField("ISBN", max_length=17, unique=True, validators=[validar_isbn])
    precio = models.DecimalField(max_digits=8, decimal_places=2,
                                 validators=[MinValueValidator(Decimal("0.01"))])
    stock = models.PositiveIntegerField(default=0)
    publicado = models.BooleanField(default=False)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="libros")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.titulo} — {self.autor}"

    def clean(self):
        errors = []
        if self.titulo and self.autor and self.titulo.lower() == self.autor.lower():
            errors.append("El título y el autor no pueden ser iguales.")
        if self.publicado and self.stock == 0:
            errors.append("Un libro publicado debe tener stock mayor a 0.")
        if errors:
            raise ValidationError(errors)

    @property
    def valor_inventario(self):
        return self.precio * self.stock
