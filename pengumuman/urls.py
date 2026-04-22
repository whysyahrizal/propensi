from django.urls import path
from . import views

app_name = 'pengumuman'

urlpatterns = [
    path('', views.daftar_pengumuman, name='daftar'),
    path('tambah/', views.tambah_pengumuman, name='tambah'),
    path('<int:pk>/', views.detail_pengumuman, name='detail'),
    path('<int:pk>/edit/', views.edit_pengumuman, name='edit'),
    path('<int:pk>/hapus/', views.hapus_pengumuman, name='hapus'),
    path('<int:pk>/toggle-status/', views.toggle_status_pengumuman, name='toggle_status'),
    path('tandai-semua-dibaca/', views.tandai_semua_dibaca, name='tandai_semua_dibaca'),
]
