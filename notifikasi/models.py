from django.db import models
from django.conf import settings
from django.utils import timezone


class Notifikasi(models.Model):
    TIPE_CHOICES = [
        ('info', 'Info'),
        ('cuti', 'Cuti'),
        ('sprin', 'Sprin'),
        ('presensi', 'Presensi'),
        ('sistem', 'Sistem'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifikasi',
        verbose_name='Penerima',
    )
    judul = models.CharField(max_length=255, verbose_name='Judul')
    pesan = models.TextField(verbose_name='Pesan')
    tipe = models.CharField(
        max_length=20, choices=TIPE_CHOICES, default='info', verbose_name='Tipe'
    )
    is_read = models.BooleanField(default=False, verbose_name='Sudah Dibaca')
    link = models.CharField(max_length=500, blank=True, verbose_name='Link Terkait')
    dibuat_pada = models.DateTimeField(default=timezone.now, verbose_name='Dibuat Pada')
    dibaca_pada = models.DateTimeField(null=True, blank=True, verbose_name='Dibaca Pada')

    # PBI-047: Email log
    email_terkirim = models.BooleanField(default=False, verbose_name='Email Terkirim')
    email_dikirim_pada = models.DateTimeField(
        null=True, blank=True, verbose_name='Email Dikirim Pada'
    )

    class Meta:
        verbose_name = 'Notifikasi'
        verbose_name_plural = 'Notifikasi'
        ordering = ['-dibuat_pada']

    def __str__(self):
        status = '✓' if self.is_read else '●'
        return f"[{status}] {self.judul} → {self.user.nama_lengkap}"

    def tandai_dibaca(self):
        """Tandai notifikasi sebagai sudah dibaca (idempotent)."""
        if not self.is_read:
            self.is_read = True
            self.dibaca_pada = timezone.now()
            self.save(update_fields=['is_read', 'dibaca_pada'])

    @property
    def tipe_icon(self):
        icons = {
            'cuti': '🗓️',
            'sprin': '📋',
            'presensi': '🕒',
            'sistem': '⚙️',
            'info': 'ℹ️',
        }
        return icons.get(self.tipe, 'ℹ️')

    @property
    def tipe_color(self):
        colors = {
            'cuti': 'blue',
            'sprin': 'purple',
            'presensi': 'green',
            'sistem': 'gray',
            'info': 'yellow',
        }
        return colors.get(self.tipe, 'gray')
