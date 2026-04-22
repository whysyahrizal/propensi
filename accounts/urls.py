from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.redirect_root, name='root'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profile_view, name='profil'),

    # Manajemen Personel
    path('personel/', views.daftar_personel_view, name='daftar_personel'),
    path('personel/<int:pk>/', views.detail_personel_view, name='detail_personel'),
    path('personel/tambah/', views.tambah_personel_view, name='tambah_personel'),
    path('personel/<int:pk>/edit/', views.edit_personel_view, name='edit_personel'),
    path('personel/<int:pk>/hapus/', views.hapus_personel_view, name='hapus_personel'),
    path('personel/<int:pk>/reaktivasi/', views.reaktivasi_personel_view, name='reaktivasi_personel'),
    path('verifikasi/', views.daftar_verifikasi_view, name='daftar_verifikasi'),
    path('personel/verifikasi/<int:pk>/detail/', views.detail_verifikasi_view, name='detail_verifikasi'),
    path('verifikasi/<int:pk>/<str:action>/', views.proses_verifikasi_view, name='proses_verifikasi'),

    # Manajemen Role
    path('roles/', views.daftar_role, name='daftar_role'),
    path('roles/tambah/', views.tambah_role, name='tambah_role'),
    path('roles/<int:pk>/', views.detail_role, name='detail_role'),
    path('roles/<int:pk>/edit/', views.edit_role, name='edit_role'),
    path('roles/<int:pk>/hapus/', views.hapus_role, name='hapus_role'),
    path('roles/<int:pk>/akses/', views.kelola_akses_menu, name='kelola_akses_menu'),

    # Manajemen Menu
    path('menus/', views.daftar_menu, name='daftar_menu'),
    path('menus/tambah/', views.tambah_menu, name='tambah_menu'),
    path('menus/<int:pk>/edit/', views.edit_menu, name='edit_menu'),  
    path('menus/<int:pk>/toggle-status/', views.toggle_status_menu, name='toggle_status_menu'),
]
