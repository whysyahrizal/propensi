from django.urls import path
from . import views

app_name = 'notifikasi'

urlpatterns = [
    path('', views.daftar_notifikasi, name='daftar'),
    path('<int:pk>/', views.detail_notifikasi, name='detail'),
    path('tandai-semua/', views.tandai_semua_dibaca, name='tandai_semua'),
]
