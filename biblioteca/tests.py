from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .forms import ContactoForm, LibroForm
from .models import Libro


class Fase1y2Formularios(TestCase):
    def test_contacto_valido_y_sanitizado(self):
        f = ContactoForm({"nombre": "ana  perez", "email": "ANA@Mail.com", "asunto": "<b>Hola</b>",
                          "mensaje": "<script>x</script>Mensaje largo de prueba"})
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data["asunto"], "Hola")
        self.assertEqual(f.cleaned_data["email"], "ana@mail.com")
        self.assertNotIn("<script>", f.cleaned_data["mensaje"])

    def test_nombre_regex_invalido(self):
        f = ContactoForm({"nombre": "R2D2!!", "email": "a@b.com", "asunto": "x", "mensaje": "mensaje de prueba"})
        self.assertIn("nombre", f.errors)

    def test_clean_cruzado_non_field_y_add_error(self):
        f = LibroForm({"titulo": "Borges", "autor": "Borges", "isbn": "9780307474728", "precio": "10", "stock": 1})
        self.assertFalse(f.is_valid())
        self.assertIn("__all__", f.errors)
        f = LibroForm({"titulo": "A", "autor": "Autor X", "isbn": "9780307474728", "precio": "10",
                       "stock": 0, "publicado": True})
        self.assertFalse(f.is_valid())
        self.assertIn("__all__", f.errors)

    def test_isbn_se_normaliza(self):
        f = LibroForm({"titulo": "A", "autor": "Autor X", "isbn": "978-0-307-47472-8", "precio": "10", "stock": 1})
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data["isbn"], "9780307474728")

    def test_post_invalido_vuelve_al_template(self):
        r = self.client.post(reverse("contacto"), {"nombre": "", "email": "mal"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "errorlist")

    def test_csrf_obligatorio(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        self.assertEqual(c.post(reverse("contacto"), {}).status_code, 403)


class Fase3Admin(TestCase):
    def setUp(self):
        call_command("seed", verbosity=0)

    def test_admin_lista_filtros_busqueda(self):
        self.client.login(username="admin", password="Admin12345!")
        r = self.client.get("/admin/biblioteca/libro/?publicado__exact=1&q=soledad")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "S/ 718.80")             # campo calculado 59.90 × 12

    def test_accion_masiva_no_publica_sin_stock(self):
        self.client.login(username="admin", password="Admin12345!")
        ids = list(Libro.objects.filter(stock=0).values_list("pk", flat=True))
        self.client.post("/admin/biblioteca/libro/", {"action": "publicar", "_selected_action": ids})
        self.assertFalse(Libro.objects.get(pk=ids[0]).publicado)

    def test_admin_rechaza_reglas_del_modelo_al_crear(self):
        self.client.login(username="admin", password="Admin12345!")
        invalid_books = [
            ({"titulo": "Autor Igual", "autor": "Autor Igual", "isbn": "9781234567897",
              "precio": "10", "stock": "1"}, "El título y el autor no pueden ser iguales."),
            ({"titulo": "Sin existencias", "autor": "Autor Z", "isbn": "9781234567880",
              "precio": "10", "stock": "0", "publicado": "on"},
             "Un libro publicado debe tener stock mayor a 0."),
        ]
        for data, error in invalid_books:
            response = self.client.post("/admin/biblioteca/libro/add/", data)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, error)
            self.assertFalse(Libro.objects.filter(isbn=data["isbn"]).exists())

    def test_edicion_en_linea_rechaza_publicar_sin_stock(self):
        self.client.login(username="admin", password="Admin12345!")
        libro = Libro.objects.get(stock=0, publicado=False)
        ordered_books = list(Libro.objects.all())
        libro_index = ordered_books.index(libro)
        data = {
            "form-TOTAL_FORMS": str(len(ordered_books)),
            "form-INITIAL_FORMS": str(len(ordered_books)),
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "_save": "Guardar",
        }
        for index, item in enumerate(ordered_books):
            data[f"form-{index}-id"] = str(item.pk)
            if item.pk == libro.pk:
                data[f"form-{index}-publicado"] = "on"

        response = self.client.post("/admin/biblioteca/libro/", data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Un libro publicado debe tener stock mayor a 0.")
        libro.refresh_from_db()
        self.assertFalse(libro.publicado)


class Fase4y5Seguridad(TestCase):
    def setUp(self):
        call_command("seed", verbosity=0)

    def test_login_required_redirige(self):
        r = self.client.get(reverse("panel"))
        self.assertRedirects(r, "/login/?next=/panel/")

    def test_flujo_completo(self):
        r = self.client.post(reverse("registro"), {"username": "nuevo", "email": "n@x.com",
                             "password1": "Clave-Segura-9876", "password2": "Clave-Segura-9876"})
        self.assertRedirects(r, reverse("panel"))
        u = User.objects.get(username="nuevo")
        self.assertTrue(u.has_perm("biblioteca.view_libro"))
        self.assertFalse(u.has_perm("biblioteca.add_libro"))
        self.assertEqual(self.client.get(reverse("libro_nuevo")).status_code, 403)   # sin rol de editor
        self.client.get(reverse("panel"))
        self.assertEqual(self.client.session["visitas_panel"], 2)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)
        self.assertEqual(self.client.get(reverse("panel")).status_code, 302)

    def test_editor_puede_crear(self):
        self.client.login(username="editor", password="Editor12345!")
        r = self.client.post(reverse("libro_nuevo"), {"titulo": "Nuevo", "autor": "Autor Z",
                             "isbn": "9781234567897", "precio": "20", "stock": 3, "publicado": "on"})
        self.assertRedirects(r, reverse("libros"))
        self.assertEqual(Libro.objects.get(isbn="9781234567897").creado_por.username, "editor")

    def test_headers_seguridad(self):
        r = self.client.get(reverse("inicio"))
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
