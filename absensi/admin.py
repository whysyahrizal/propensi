from django.contrib import admin
from .models import RekorAbsensi


@admin.register(RekorAbsensi)
class RekorAbsensiAdmin(admin.ModelAdmin):
    list_display = ['personel', 'tanggal', 'status', 'waktu_masuk', 'waktu_keluar', 'sprin']
    list_filter = ['status', 'tanggal', 'personel__satker']
    search_fields = ['personel__nama_lengkap', 'personel__nrp']
    date_hierarchy = 'tanggal'
    ordering = ['-tanggal']
