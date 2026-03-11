from django.urls import path
from .views import (
    PersonelListView,
    PersonelDetailView,
    PersonelCreateView,
    PersonelUpdateView,
    PersonelDeleteView,
)

urlpatterns = [
    path('', PersonelListView.as_view(), name='personel_list'),
    path('tambah/', PersonelCreateView.as_view(), name='personel_create'),
    path('<int:pk>/', PersonelDetailView.as_view(), name='personel_detail'),
    path('<int:pk>/edit/', PersonelUpdateView.as_view(), name='personel_update'),
    path('<int:pk>/delete/', PersonelDeleteView.as_view(), name='personel_delete'),
]