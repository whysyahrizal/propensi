from django.urls import path
from django.views.generic import RedirectView

app_name = 'presensi'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='absensi:dashboard', permanent=False), name='dashboard'),
    path('checkin/', RedirectView.as_view(pattern_name='absensi:checkin', permanent=False), name='checkin'),
    path('checkout/', RedirectView.as_view(pattern_name='absensi:checkout', permanent=False), name='checkout'),
    path('history/', RedirectView.as_view(pattern_name='absensi:history', permanent=False), name='history'),
    path('rekap/', RedirectView.as_view(pattern_name='absensi:rekap_admin', permanent=False), name='rekap_admin'),
    path('rekap/pribadi/', RedirectView.as_view(pattern_name='absensi:rekap_pribadi', permanent=False), name='rekap_pribadi'),
]
