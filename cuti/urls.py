from django.urls import path
from . import views

app_name = 'cuti'

urlpatterns = [
    path('ajukan/', views.LeaveRequestCreateView.as_view(), name='ajukan'),
    path('riwayat/', views.LeaveHistoryListView.as_view(), name='riwayat'),
    path('kelola/', views.LeaveAdminListView.as_view(), name='kelola'),
    path('detail/<int:pk>/', views.LeaveDetailView.as_view(), name='detail'),
    path('edit/<int:pk>/', views.LeaveRequestUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.LeaveRequestDeleteView.as_view(), name='delete'),
]
