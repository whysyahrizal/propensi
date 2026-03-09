from django.urls import path
from . import views

app_name = 'notifikasi'

urlpatterns = [
    path('', views.daftar_notifikasi, name='daftar'),
    path('<int:pk>/baca/', views.tandai_baca, name='tandai_baca'),
    path('baca-semua/', views.baca_semua, name='baca_semua'),
]
