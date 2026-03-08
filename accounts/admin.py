from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Satker, Personel


@admin.register(Satker)
class SatkerAdmin(admin.ModelAdmin):
    list_display = ['kode', 'nama', 'keterangan']
    search_fields = ['kode', 'nama']


@admin.register(Personel)
class PersonelAdmin(UserAdmin):
    list_display = ['nrp', 'nama_lengkap', 'pangkat', 'satker', 'role', 'is_active']
    list_filter = ['role', 'pangkat', 'satker', 'is_active']
    search_fields = ['nrp', 'nama_lengkap', 'email']
    ordering = ['nama_lengkap']

    fieldsets = (
        (None, {'fields': ('nrp', 'password')}),
        ('Informasi Personel', {'fields': ('nama_lengkap', 'pangkat', 'jabatan', 'satker', 'email', 'no_hp', 'foto')}),
        ('Role & Akses', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('nrp', 'nama_lengkap', 'pangkat', 'satker', 'role', 'password1', 'password2'),
        }),
    )
