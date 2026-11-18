from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("contacto/", views.contacto, name="contacto"),
    path("libros/", views.LibroListView.as_view(), name="libros"),
    path("libros/nuevo/", views.LibroCreateView.as_view(), name="libro_nuevo"),
    path("registro/", views.registro, name="registro"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),   # POST en Django 5
    path("panel/", views.panel, name="panel"),
]
