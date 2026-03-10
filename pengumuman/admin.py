from django.contrib import admin
from .models import Pengumuman


@admin.register(Pengumuman)
class PengumumanAdmin(admin.ModelAdmin):
    list_display = ['judul', 'dibuat_oleh', 'is_published', 'dibuat_pada']
    list_filter = ['is_published']
    search_fields = ['judul', 'konten']
    ordering = ['-dibuat_pada']
