"""python manage.py seed → crea roles, usuarios demo y libros de ejemplo."""
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

from biblioteca.models import Libro


class Command(BaseCommand):
    help = "Crea grupos (Lectores/Editores), usuarios demo y datos de ejemplo"

    def handle(self, *args, **opts):
        lectores, _ = Group.objects.get_or_create(name="Lectores")
        editores, _ = Group.objects.get_or_create(name="Editores")
        lectores.permissions.set(Permission.objects.filter(codename="view_libro"))
        editores.permissions.set(Permission.objects.filter(
            codename__in=["view_libro", "add_libro", "change_libro"]))

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "Admin12345!")
        ed, creado = User.objects.get_or_create(username="editor", defaults={"email": "editor@example.com"})
        if creado:
            ed.set_password("Editor12345!")
            ed.is_staff = True          # puede entrar al admin, con permisos limitados
            ed.save()
        ed.groups.add(editores)
        lec, creado = User.objects.get_or_create(username="lector", defaults={"email": "lector@example.com"})
        if creado:
            lec.set_password("Lector12345!")
            lec.save()
        lec.groups.add(lectores)

        demo = [("Cien años de soledad", "Gabriel García Márquez", "9780307474728", "59.90", 12, True),
                ("La ciudad y los perros", "Mario Vargas Llosa", "9788420471839", "49.50", 8, True),
                ("Los ríos profundos", "José María Arguedas", "9788437604947", "39.00", 0, False)]
        for t, a, i, p, s, pub in demo:
            Libro.objects.get_or_create(isbn=i, defaults=dict(titulo=t, autor=a, precio=p, stock=s,
                                                               publicado=pub, creado_por=ed))
        self.stdout.write(self.style.SUCCESS("Listo: admin / editor / lector (ver README)."))
