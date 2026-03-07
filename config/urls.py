from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('/personel/')),
    path('personel/', include('personel.urls')),
]