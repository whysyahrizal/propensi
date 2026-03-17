from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from importlib.util import find_spec

urlpatterns = [
    path('admin/', admin.site.urls),
    path('personel/', include('personel.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('sprin/', include('sprin.urls')),
    path('absensi/', include('absensi.urls')),
    path('cuti/', include('manajemen_cuti.urls')),
    path('presensi/', include('presensi.urls')),
    path('locations/', include('locations.urls')),
    path('pengumuman/', include('pengumuman.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='root'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Optional modules: include only when app URL module exists.
for prefix, module in [
    ('pengumuman/', 'pengumuman.urls'),
    ('notifikasi/', 'notifikasi.urls'),
]:
    app_label = module.split('.', 1)[0]
    if find_spec(app_label) and find_spec(module):
        urlpatterns.append(path(prefix, include(module)))
