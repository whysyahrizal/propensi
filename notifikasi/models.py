from django.db import models
from django.conf import settings


class Notifikasi(models.Model):
    TIPE_CHOICES = [
        ('cuti_status', 'Update Status Cuti'),
        ('sprin_baru', 'Sprin Baru'),
        ('pengajuan_masuk', 'Pengajuan Cuti Masuk'),
        ('surat_diterbitkan', 'Surat Resmi Diterbitkan'),
        ('umum', 'Umum'),
    ]

    penerima = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifikasi', verbose_name='Penerima'
    )
    judul = models.CharField(max_length=200, verbose_name='Judul')
    pesan = models.TextField(verbose_name='Pesan')
    tipe = models.CharField(max_length=30, choices=TIPE_CHOICES, default='umum', verbose_name='Tipe')
    url_ref = models.CharField(max_length=300, blank=True, verbose_name='URL Referensi')
    is_read = models.BooleanField(default=False, verbose_name='Sudah Dibaca')
    dibuat_pada = models.DateTimeField(auto_now_add=True, verbose_name='Dibuat Pada')

    class Meta:
        verbose_name = 'Notifikasi'
        verbose_name_plural = 'Notifikasi'
        ordering = ['-dibuat_pada']

    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"{status} [{self.get_tipe_display()}] {self.judul}"
