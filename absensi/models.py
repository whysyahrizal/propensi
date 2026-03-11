from django.db import models
from django.conf import settings


class RekorAbsensi(models.Model):
    STATUS_CHOICES = [
        ('hadir', 'Hadir'),
        ('sakit', 'Sakit'),
        ('izin', 'Izin'),
        ('cuti', 'Cuti'),
        ('alpa', 'Alpa'),
    ]

    personel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='rekap_absensi', verbose_name='Personel'
    )
    sprin = models.ForeignKey(
        'sprin.Sprin', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='absensi',
        verbose_name='Sprin Terkait'
    )
    tanggal = models.DateField(verbose_name='Tanggal')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='hadir', verbose_name='Status')

    # Check-in
    waktu_masuk = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Masuk')
    lat_masuk = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='Latitude Masuk')
    lon_masuk = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='Longitude Masuk')
    foto_masuk = models.ImageField(upload_to='absensi/foto/', blank=True, null=True, verbose_name='Foto Masuk (Selfie)')

    # Check-out
    waktu_keluar = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Keluar')
    lat_keluar = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='Latitude Keluar')
    lon_keluar = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='Longitude Keluar')
    foto_keluar = models.ImageField(upload_to='absensi/foto/', blank=True, null=True, verbose_name='Foto Keluar (Selfie)')

    catatan = models.TextField(blank=True, verbose_name='Catatan')
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rekap Absensi'
        verbose_name_plural = 'Rekap Absensi'
        ordering = ['-tanggal', '-waktu_masuk']
        unique_together = ('personel', 'tanggal', 'sprin')

    def __str__(self):
        return f"{self.personel} — {self.tanggal} ({self.get_status_display()})"
