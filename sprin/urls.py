from django.urls import path
from . import views

app_name = 'sprin'

urlpatterns = [
    path('', views.daftar_sprin, name='daftar'),
    path('tambah/', views.tambah_sprin, name='tambah'),
    path('<int:pk>/', views.detail_sprin, name='detail'),
    path('<int:pk>/edit/', views.edit_sprin, name='edit'),
    path('<int:pk>/hapus/', views.hapus_sprin, name='hapus'),
]
