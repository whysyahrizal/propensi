from django.contrib import admin
from .models import Notifikasi


@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ['judul', 'user', 'tipe', 'is_read', 'email_terkirim', 'dibuat_pada']
    list_filter = ['tipe', 'is_read', 'email_terkirim']
    search_fields = ['judul', 'pesan', 'user__nama_lengkap', 'user__nrp']
    readonly_fields = ['dibuat_pada', 'dibaca_pada', 'email_dikirim_pada']
    ordering = ['-dibuat_pada']
