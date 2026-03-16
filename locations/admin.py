from django.contrib import admin
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'latitude', 'longitude', 'radius', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name',)
