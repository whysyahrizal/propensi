from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.redirect_root, name='root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profile_view, name='profil'),
    # Manajemen Personel
    path('personel/', views.daftar_personel_view, name='daftar_personel'),
    path('personel/tambah/', views.tambah_personel_view, name='tambah_personel'),
    path('personel/<int:pk>/edit/', views.edit_personel_view, name='edit_personel'),
    path('personel/<int:pk>/hapus/', views.hapus_personel_view, name='hapus_personel'),
    # EPIC03 — Manajemen Role (PBI-011 to PBI-015)
    path('roles/', views.daftar_role, name='daftar_role'),
    path('roles/tambah/', views.tambah_role, name='tambah_role'),
    path('roles/<int:pk>/', views.detail_role, name='detail_role'),
    path('roles/<int:pk>/edit/', views.edit_role, name='edit_role'),
    path('roles/<int:pk>/hapus/', views.hapus_role, name='hapus_role'),
]
