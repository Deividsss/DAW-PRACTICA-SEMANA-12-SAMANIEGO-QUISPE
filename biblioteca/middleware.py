"""FASE 4 · Middleware personalizado.

Orden: en MIDDLEWARE el request baja de arriba→abajo y la response sube de abajo→arriba.
Este middleware va al final: ve el request ya autenticado y la response antes de que
salga por los demás middlewares.
"""
import logging
import time

log = logging.getLogger("auditoria")


class AuditoriaMiddleware:
    def __init__(self, get_response):           # se ejecuta una vez al arrancar
        self.get_response = get_response

    def __call__(self, request):                # se ejecuta en cada request
        inicio = time.perf_counter()
        response = self.get_response(request)   # → vista → response
        ms = (time.perf_counter() - inicio) * 1000

        user = request.user.get_username() if request.user.is_authenticated else "anónimo"
        log.info("%s %s · %s · usuario=%s · %.1f ms", request.method, request.path, response.status_code, user, ms)

        # Historial en sesión (lista mutable ⇒ hay que avisar a Django)
        if request.user.is_authenticated and not request.path.startswith(("/admin/", "/static/")):
            rutas = request.session.get("ultimas_rutas", [])
            rutas = (rutas + [request.path])[-5:]
            request.session["ultimas_rutas"] = rutas
            request.session.modified = True

        # Cabeceras de seguridad (el admin usa scripts inline, por eso se excluye)
        if not request.path.startswith("/admin/"):
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'",
            )
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response
