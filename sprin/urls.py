from django.urls import path
from . import views

app_name = 'sprin'

urlpatterns = [
    path('', views.all_sprin, name='daftar'),
    path('pimpinan/', views.pimpinan_list, name='pimpinan_list'), # Halaman pimpinan
    path('create/', views.create_sprin, name='create_sprin'),
    path('pimpinan/', views.pimpinan_list, name='pimpinan_list'),
    path('disetujui/', views.disetujui_list, name='disetujui_list'),
    path('set-role/', views.set_role, name='set_role'),
    path('<uuid:pk>/', views.detail_sprin, name='detail_sprin'), # Detail umum
    path('<uuid:pk>/aksi/', views.aksi_sprin, name='aksi_sprin'), # Proses approve
    path('<uuid:pk>/upload/', views.upload_file_sprin, name='upload_file_sprin'), # Upload file hasil scan (Admin SDM)
]