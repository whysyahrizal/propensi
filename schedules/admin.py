from django.contrib import admin

from .models import ShiftSchedule, ShiftSchedulePersonnel


class ShiftSchedulePersonnelInline(admin.TabularInline):
    model = ShiftSchedulePersonnel
    extra = 1
    autocomplete_fields = ('personel',)


@admin.register(ShiftSchedule)
class ShiftScheduleAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift_type', 'location', 'personnel_count', 'created_by')
    list_filter = ('shift_type', 'date', 'location')
    search_fields = ('location__name',)
    autocomplete_fields = ('location', 'created_by')
    inlines = [ShiftSchedulePersonnelInline]


@admin.register(ShiftSchedulePersonnel)
class ShiftSchedulePersonnelAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'personel', 'created_at')
    list_filter = ('schedule__date', 'schedule__shift_type')
    search_fields = ('personel__nama_lengkap', 'personel__nrp', 'schedule__location__name')
    autocomplete_fields = ('schedule', 'personel')
