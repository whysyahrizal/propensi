from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('api/ringkasan/', views.api_ringkasan_harian, name='api_ringkasan'),
    path('api/informasi-aktivitas/', views.api_informasi_aktivitas, name='api_informasi_aktivitas'),
]
