from django.contrib import admin
from .models import PengajuanCuti


@admin.register(PengajuanCuti)
class PengajuanCutiAdmin(admin.ModelAdmin):
    list_display = ['personel', 'jenis_cuti', 'tanggal_mulai', 'tanggal_selesai', 'status', 'diajukan_pada']
    list_filter = ['status', 'jenis_cuti', 'tanggal_mulai']
    search_fields = ['personel__nama_lengkap', 'personel__nrp']
    readonly_fields = ['diajukan_pada']
    ordering = ['-diajukan_pada']
