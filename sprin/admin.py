from django.contrib import admin
from .models import Sprin, PersonelSprin


class PersonelSprinInline(admin.TabularInline):
    model = PersonelSprin
    extra = 1


@admin.register(Sprin)
class SprinAdmin(admin.ModelAdmin):
    list_display = ['nomor', 'perihal', 'tanggal', 'status', 'dibuat_oleh']
    list_filter = ['status', 'tanggal']
    search_fields = ['nomor', 'perihal']
    inlines = [PersonelSprinInline]
    ordering = ['-tanggal']


@admin.register(PersonelSprin)
class PersonelSprinAdmin(admin.ModelAdmin):
    list_display = ['sprin', 'personel', 'jabatan_dalam_sprin', 'nomor_urut']
    list_filter = ['sprin']
    search_fields = ['personel__nama_lengkap', 'personel__nrp']
