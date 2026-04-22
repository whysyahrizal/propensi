from django.urls import path
from . import views

app_name = 'presensi'

urlpatterns = [
    path('', views.presensi_dashboard, name='dashboard'),
    path('checkin/', views.checkin_process, name='checkin'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('history/', views.history, name='history'),
    path('rekap/', views.rekap_admin, name='rekap_admin'),
    path('rekap/pribadi/', views.rekap_pribadi, name='rekap_pribadi'),
]
