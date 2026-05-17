from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('api/ringkasan/', views.api_ringkasan_harian, name='api_ringkasan'),
    path('api/informasi/', views.api_informasi_aktivitas, name='api_informasi'),
    
    path('kehadiran-superadmin/', views.superadmin_dashboard_view, name='dashboard_kehadiran_superadmin'),
    path('kehadiran-unit/', views.superadmin_unit_detail_view, name='dashboard_kehadiran_unit'),
    path('kehadiran-pimpinan/', views.pimpinan_dashboard_view, name='dashboard_kehadiran_pimpinan'),
    path('monitoring-sprin/', views.monitoring_sprin_main_view, name='monitoring_sprin_main'),
    path('monitoring-sprin/<int:sprin_id>/detail/', views.monitoring_sprin_detail_view, name='monitoring_sprin_detail'),
]