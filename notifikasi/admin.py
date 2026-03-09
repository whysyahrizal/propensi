from django.contrib import admin
from .models import Notifikasi


@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ['penerima', 'judul', 'tipe', 'is_read', 'dibuat_pada']
    list_filter = ['tipe', 'is_read']
    search_fields = ['penerima__nama_lengkap', 'judul']
    ordering = ['-dibuat_pada']
