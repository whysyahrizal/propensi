from django.urls import path
from . import views

app_name = 'absensi'

urlpatterns = [
    path('', views.rekap_absensi, name='rekap'),
    path('checkin/', views.checkin_view, name='checkin'),
    path('checkout/', views.checkout_view, name='checkout'),
]
