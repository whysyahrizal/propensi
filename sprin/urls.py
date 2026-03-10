from django.urls import path
from . import views

app_name = 'sprin'

urlpatterns = [
    # PBI-024/026: Daftar sprin (semua role, filter berbeda)
    path('', views.daftar_sprin, name='daftar'),

    # PBI-021: Buat sprin baru
    path('tambah/', views.tambah_sprin, name='tambah'),

    # PBI-025/027: Detail sprin
    path('<int:pk>/', views.detail_sprin, name='detail'),

    # PBI-022: Edit sprin (hanya draft)
    path('<int:pk>/edit/', views.edit_sprin, name='edit'),

    # Workflow: ajukan dari draft → menunggu_paraf
    path('<int:pk>/ajukan/', views.ajukan_sprin, name='ajukan'),

    # PBI-023: Cancel sprin
    path('<int:pk>/batal/', views.batal_sprin, name='batal'),

    # PBI-028: Approve/Reject sprin (pimpinan)
    path('<int:pk>/aksi/', views.aksi_sprin, name='aksi'),

    # Tambah personel ke sprin
    path('<int:pk>/personel/tambah/', views.tambah_personel_sprin, name='tambah_personel'),

    # Hapus sprin (hanya draft)
    path('<int:pk>/hapus/', views.hapus_sprin, name='hapus'),
]
