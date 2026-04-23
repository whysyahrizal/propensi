from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('', views.location_list, name='daftar'),
    path('tambah/', views.location_create, name='tambah'),
    path('<int:pk>/edit/', views.location_edit, name='edit'),
    path('peta/', views.location_map, name='peta'),
    path('api/geocode/', views.geocode_search, name='geocode'),
]
