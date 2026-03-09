from django.db import models
from django.conf import settings


class Pengumuman(models.Model):
    judul = models.CharField(max_length=300, verbose_name='Judul')
    konten = models.TextField(verbose_name='Isi Konten')
    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='pengumuman',
        verbose_name='Dibuat Oleh'
    )
    lampiran = models.FileField(
        upload_to='pengumuman/lampiran/', blank=True, null=True,
        verbose_name='Lampiran (Gambar/PDF)'
    )
    is_published = models.BooleanField(default=True, verbose_name='Dipublikasikan')
    dibuat_pada = models.DateTimeField(auto_now_add=True, verbose_name='Dibuat Pada')
    diperbarui_pada = models.DateTimeField(auto_now=True, verbose_name='Diperbarui Pada')

    class Meta:
        verbose_name = 'Pengumuman'
        verbose_name_plural = 'Pengumuman'
        ordering = ['-dibuat_pada']

    def __str__(self):
        return self.judul
