from django.urls import path
from . import views

app_name = 'absensi'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('checkin/', views.checkin_view, name='checkin'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('riwayat/', views.history_view, name='history'),
    path('rekap/', views.rekap_admin_view, name='rekap_admin'),
    path('rekap/pribadi/', views.rekap_pribadi_view, name='rekap_pribadi'),
]
