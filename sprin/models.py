from django.db import models
from django.conf import settings


class Sprin(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('menunggu_paraf', 'Menunggu Paraf'),
        ('aktif', 'Aktif'),
        ('selesai', 'Selesai'),
    ]

    nomor = models.CharField(max_length=100, unique=True, verbose_name='Nomor Sprin')
    tanggal = models.DateField(verbose_name='Tanggal')
    perihal = models.CharField(max_length=300, verbose_name='Perihal / Operasi')
    dasar = models.TextField(blank=True, verbose_name='Dasar')
    isi_perintah = models.TextField(blank=True, verbose_name='Isi Perintah')
    pejabat_penandatangan = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sprin_ditandatangani',
        verbose_name='Pejabat Penandatangan'
    )
    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='sprin_dibuat',
        verbose_name='Dibuat Oleh'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Status')
    file_sprin = models.FileField(upload_to='sprin/', blank=True, null=True, verbose_name='File Sprin (PDF)')
    # Geolocation: lokasi penugasan (titik pusat)
    lat_lokasi = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='Latitude Lokasi')
    lon_lokasi = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='Longitude Lokasi')
    radius_meter = models.IntegerField(default=100, verbose_name='Radius Presensi (meter)')
    waktu_mulai = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Mulai')
    waktu_selesai = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Selesai')
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Surat Perintah (Sprin)'
        verbose_name_plural = 'Surat Perintah (Sprin)'
        ordering = ['-tanggal', '-dibuat_pada']

    def __str__(self):
        return f"{self.nomor} — {self.perihal}"


class PersonelSprin(models.Model):
    sprin = models.ForeignKey(Sprin, on_delete=models.CASCADE, related_name='personel_list', verbose_name='Sprin')
    personel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='penugasan', verbose_name='Personel'
    )
    nomor_urut = models.PositiveIntegerField(default=1, verbose_name='Nomor Urut')
    jabatan_dalam_sprin = models.CharField(max_length=200, blank=True, verbose_name='Jabatan dalam Sprin')
    keterangan = models.CharField(max_length=300, blank=True, verbose_name='Keterangan')

    class Meta:
        verbose_name = 'Personel dalam Sprin'
        verbose_name_plural = 'Personel dalam Sprin'
        unique_together = ('sprin', 'personel')
        ordering = ['nomor_urut']

    def __str__(self):
        return f"{self.personel} → {self.sprin.nomor}"
