from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('/personel/')),
    path('personel/', include('personel.urls')),
    path('sprin/', include('sprin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
