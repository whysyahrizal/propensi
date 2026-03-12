from django.db import models


class Location(models.Model):
    TYPE_CHOICES = [
        ('pos', 'Pos'),
        ('mako', 'Mako'),
    ]

    name = models.CharField(max_length=255, unique=True, verbose_name='Nama Lokasi')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Tipe')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, verbose_name='Latitude')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, verbose_name='Longitude')
    radius = models.IntegerField(default=100, verbose_name='Radius (meter)')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Dibuat Pada')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Diperbarui Pada')

    class Meta:
        verbose_name = 'Wilayah Penugasan'
        verbose_name_plural = 'Wilayah Penugasan'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
