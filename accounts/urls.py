from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.redirect_root, name='root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profil/', views.profile_view, name='profil'),
    path('personel/', views.daftar_personel_view, name='daftar_personel'),
    path('personel/tambah/', views.tambah_personel_view, name='tambah_personel'),
    path('personel/<int:pk>/edit/', views.edit_personel_view, name='edit_personel'),
    path('personel/<int:pk>/hapus/', views.hapus_personel_view, name='hapus_personel'),
]
