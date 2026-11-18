import logging
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import ContactoForm, LibroForm, RegistroForm
from .models import Libro

log = logging.getLogger("auditoria")


def inicio(request):
    return render(request, "biblioteca/inicio.html")


# ---------------- FASE 1: formulario clásico (instanciar → validar → cleaned_data)
def contacto(request):
    if request.method == "POST":
        form = ContactoForm(request.POST)          # siempre pasar por el Form
        if form.is_valid():                        # validar antes de usar datos
            datos = form.cleaned_data
            log.info("Contacto recibido de %s <%s>: %s", datos["nombre"], datos["email"], datos["asunto"])
            messages.success(request, "Mensaje enviado. Gracias por escribirnos.")
            return redirect("contacto")
    else:
        form = ContactoForm()
    return render(request, "biblioteca/contacto.html", {"form": form})


# ---------------- FASE 1: ModelForm + permisos (Fase 4)
class LibroListView(LoginRequiredMixin, ListView):
    model = Libro
    template_name = "biblioteca/libro_list.html"
    context_object_name = "libros"

    def get_queryset(self):
        return Libro.objects.select_related("creado_por")


class LibroCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "biblioteca.add_libro"   # autorización por permiso/rol
    form_class = LibroForm
    template_name = "biblioteca/libro_form.html"
    success_url = reverse_lazy("libros")

    def form_valid(self, form):
        libro = form.save(commit=False)            # is_valid() ya se ejecutó
        libro.creado_por = self.request.user
        libro.save()
        messages.success(self.request, f"«{libro.titulo}» guardado.")
        return redirect(self.success_url)


# ---------------- FASE 4/5: registro, panel, sesión
def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name="Lectores")
            grupo.permissions.add(Permission.objects.get(codename="view_libro"))
            user.groups.add(grupo)                 # rol por defecto: solo lectura
            login(request, user)
            messages.success(request, "Cuenta creada. Bienvenido.")
            return redirect("panel")
    else:
        form = RegistroForm()
    return render(request, "registration/registro.html", {"form": form})


@login_required
def panel(request):
    request.session["visitas_panel"] = request.session.get("visitas_panel", 0) + 1
    return render(request, "biblioteca/panel.html", {
        "visitas": request.session["visitas_panel"],
        "rutas": request.session.get("ultimas_rutas", []),
        "puede_crear": request.user.has_perm("biblioteca.add_libro"),
        "roles": ", ".join(request.user.groups.values_list("name", flat=True)) or "sin rol",
    })
