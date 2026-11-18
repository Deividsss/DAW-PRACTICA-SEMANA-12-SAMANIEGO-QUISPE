# Semana 12 · Django: Formularios, Admin, Middleware, Sesiones y Autenticación

Proyecto **Biblioteca** (modelo `Libro`) con diseño minimalista. Cada fase de la guía tiene su archivo y su prueba.

## Puesta en marcha

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed             # roles + usuarios demo + 3 libros
python manage.py runserver
```

| Usuario | Clave | Rol |
|---|---|---|
| `admin` | `Admin12345!` | Superusuario |
| `editor` | `Editor12345!` | Editores (crea/edita libros, entra al admin) |
| `lector` | `Lector12345!` | Lectores (solo ver) |

Pruebas automáticas: `python manage.py test` (12 pruebas, todas pasan).

---

## PASO A PASO (según el cuadro de la guía)

### Fase 1 · Formularios y plantillas — 10 min
**Archivos:** `biblioteca/forms.py`, `biblioteca/views.py`, `biblioteca/templates/biblioteca/contacto.html`, `libro_form.html`

1. `forms.py`: `ContactoForm` (formulario clásico) y `LibroForm` (`ModelForm`).
2. Vista `contacto`: `form = ContactoForm(request.POST)` → `form.is_valid()` → `cleaned_data`. **Nunca** se lee `request.POST` directamente para guardar.
3. `LibroCreateView`: `form.save(commit=False)` solo después de `is_valid()`.
4. Plantillas: `{% csrf_token %}`, `{{ form.as_p }}`, `{{ form.errors }}` / `non_field_errors`.
5. Ruta POST en `urls.py`: `/contacto/` y `/libros/nuevo/`.

**Probar:** abre `/contacto/`, envía vacío y verás los errores; en DevTools → Network confirma el campo `csrfmiddlewaretoken`.

### Fase 2 · Validación y sanitización — 10 min
**Archivos:** `biblioteca/validators.py`, `biblioteca/forms.py`

1. Validadores regex: `validar_nombre`, `validar_isbn`.
2. `sanitize_input()`: `strip_tags` + `strip()` + colapsa espacios + `lower()` opcional.
3. `clean_<campo>()`: `clean_titulo`, `clean_autor`, `clean_isbn` (normaliza y verifica duplicado).
4. `clean()` cruzado: título ≠ autor → error global (`__all__`); publicado con stock 0 → `self.add_error("stock", …)`.
5. Niveles: campo → formulario → modelo (`full_clean` automático en ModelForm).

**Probar:** en `/libros/nuevo/` (con `editor`) pon título = autor, y luego publicado con stock 0. Compara el error general contra el error por campo.

### Fase 3 · Django Admin — 10 min
**Archivo:** `biblioteca/admin.py`

1. `@admin.register(Libro)` con `LibroAdmin`.
2. `list_display`, `list_filter`, `search_fields`, `date_hierarchy`, `list_editable`.
3. Campo calculado con `@admin.display` → `valor_inventario`.
4. `readonly_fields = ("creado_por", "creado")` y `fields` explícito (sin campos sensibles).
5. `actions`: `publicar` y `despublicar` (reciben `request, queryset`).
6. `list_select_related = ("creado_por",)` para evitar consultas N+1.

**Probar:** `/admin/` con `admin`; filtra, busca «soledad», selecciona libros y ejecuta la acción.

### Fase 4 · Middleware y sesiones — 10 min
**Archivos:** `biblioteca/middleware.py`, `config/settings.py`, `biblioteca/views.py`

1. `AuditoriaMiddleware` con `__init__(get_response)` y `__call__(request)`; devuelve siempre la response.
2. Registrado al final de `MIDDLEWARE` (el request baja, la response sube).
3. `settings.py`: `SESSION_ENGINE`, `SESSION_COOKIE_AGE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `LOGIN_URL`.
4. `@login_required` en `panel`; `LoginRequiredMixin` y `PermissionRequiredMixin` (`biblioteca.add_libro`) en las vistas de libros.
5. Sesión: contador `visitas_panel` y lista `ultimas_rutas` con `request.session.modified = True`.

**Probar:** entra a `/panel/` sin sesión → redirige a login. Con `lector`, `/libros/nuevo/` da 403; con `editor`, funciona.

### Fase 5 · Integración y auditoría — 5 min
1. Flujo: **registro → login → panel (restringido) → admin → logout** (el logout es POST).
2. DevTools → Application → Cookies: `sessionid` (HttpOnly) y `csrftoken`.
3. DevTools → Network → Response Headers: `X-Frame-Options: DENY`, `Content-Security-Policy`, `X-Content-Type-Options`, `Permissions-Policy`.
4. Logs en consola y en `logs/auditoria.log`.
5. Seguridad de despliegue:
   ```bash
   export DJANGO_DEBUG=0
   export DJANGO_ALLOWED_HOSTS="tusitio.com"
   export DJANGO_SECRET_KEY="<clave larga y aleatoria>"
   python manage.py check --deploy
   ```

---

## Evidencias a entregar
- [ ] Captura de cada fase (formulario con errores, admin con filtros/acción, 403 vs acceso del editor, cookies, headers, `check --deploy`).
- [ ] Enlace al repositorio de GitHub:
  ```bash
  git init && git add . && git commit -m "Semana 12" 
  git branch -M main && git remote add origin <URL> && git push -u origin main
  ```

## Estructura
```
config/            settings, urls
biblioteca/        models, forms, validators, views, admin, middleware, tests
  management/commands/seed.py
  static/biblioteca/estilo.css
templates/         base.html, 403.html, registration/
```
