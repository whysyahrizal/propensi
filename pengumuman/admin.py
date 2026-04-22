from django.contrib import admin
from .models import Pengumuman

@admin.register(Pengumuman)
class PengumumanAdmin(admin.ModelAdmin):
    list_display = ('judul', 'tanggal_publikasi', 'is_active', 'status_tayang')
    search_fields = ('judul', 'isi')
    list_filter = ('is_active', 'tanggal_publikasi')
