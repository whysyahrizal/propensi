from django.contrib import admin
from .models import Unit, Personel

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'nama')
    search_fields = ('nama',)


@admin.register(Personel)
class PersonelAdmin(admin.ModelAdmin):
    list_display = ('id', 'nama', 'nip', 'unit', 'is_active')
    list_filter = ('unit', 'is_active')
    search_fields = ('nama', 'nip')