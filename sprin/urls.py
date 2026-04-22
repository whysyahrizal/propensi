from django.urls import path
from . import views

app_name = 'sprin'

urlpatterns = [
    path('', views.all_sprin, name='daftar'),
    path('pimpinan/', views.pimpinan_list, name='pimpinan_list'), # Halaman pimpinan
    path('create/', views.create_sprin, name='create_sprin'),
    path('tambah/', views.create_sprin, name='tambah'),
    path('pimpinan/', views.pimpinan_list, name='pimpinan_list'),
    path('disetujui/', views.disetujui_list, name='disetujui_list'),
    path('set-role/', views.set_role, name='set_role'),
    path('<uuid:pk>/', views.detail_sprin, name='detail_sprin'),
    path('<uuid:pk>/', views.detail_sprin, name='detail'),
    path('<uuid:pk>/aksi/', views.aksi_sprin, name='aksi_sprin'),
    path('<uuid:pk>/aksi/', views.aksi_sprin, name='aksi'),
    path('<uuid:pk>/edit/', views.detail_sprin, name='edit'),
    path('<uuid:pk>/ajukan/', views.detail_sprin, name='ajukan'),
    path('<uuid:pk>/batal/', views.detail_sprin, name='batal'),
    path('<uuid:pk>/hapus/', views.detail_sprin, name='hapus'),
    path('<uuid:pk>/tambah-personel/', views.detail_sprin, name='tambah_personel'),
    path('<uuid:pk>/upload/', views.upload_file_sprin, name='upload_file_sprin'),
]
