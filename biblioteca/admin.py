"""FASE 3 · Django Admin"""
from django.contrib import admin, messages

from .models import Libro


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "isbn", "precio", "stock", "valor_inventario", "publicado", "creado_por")
    list_filter = ("publicado", "creado", "autor")
    search_fields = ("titulo", "autor", "isbn")
    list_editable = ("publicado",)
    list_select_related = ("creado_por",)          # evita N+1 en la lista
    date_hierarchy = "creado"
    ordering = ("-creado",)
    # Visibilidad controlada: solo los campos necesarios (nada sensible)
    fields = ("titulo", "autor", "isbn", "precio", "stock", "publicado", "creado_por", "creado")
    readonly_fields = ("creado_por", "creado")     # solo lectura: no se editan ni se guardan desde el form
    actions = ["publicar", "despublicar"]

    # Campo calculado
    @admin.display(description="Valor inventario", ordering="precio")
    def valor_inventario(self, obj):
        return f"S/ {obj.valor_inventario:,.2f}"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

    # Acciones masivas: reciben (modeladmin, request, queryset)
    @admin.action(description="Publicar libros seleccionados")
    def publicar(self, request, queryset):
        n = queryset.filter(stock__gt=0).update(publicado=True)
        self.message_user(request, f"{n} libro(s) publicados.", messages.SUCCESS)

    @admin.action(description="Despublicar libros seleccionados")
    def despublicar(self, request, queryset):
        n = queryset.update(publicado=False)
        self.message_user(request, f"{n} libro(s) despublicados.", messages.WARNING)


admin.site.site_header = "Biblioteca · Administración"
admin.site.site_title = "Biblioteca"
