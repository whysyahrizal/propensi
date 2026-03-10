from django.urls import path
from . import views

app_name = 'cuti'

urlpatterns = [
    path('', views.daftar_cuti, name='daftar'),
    path('ajukan/', views.ajukan_cuti, name='ajukan'),
    path('<int:pk>/', views.detail_cuti, name='detail'),
    path('<int:pk>/setujui/', views.setujui_cuti, name='setujui'),
    path('<int:pk>/tolak/', views.tolak_cuti, name='tolak'),
    path('<int:pk>/upload-surat/', views.upload_surat_cuti, name='upload_surat'),
    path('monitoring/', views.monitoring_cuti, name='monitoring'),
]
