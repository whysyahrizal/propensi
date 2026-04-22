from django.db import models
from django.utils import timezone
from accounts.models import Personel

class Pengumuman(models.Model):
    judul = models.CharField(max_length=255)
    isi = models.TextField()
    tanggal_publikasi = models.DateTimeField(default=timezone.now)
    periode_mulai = models.DateTimeField(null=True, blank=True)
    periode_selesai = models.DateTimeField(null=True, blank=True)
    dibuat_oleh = models.ForeignKey(Personel, on_delete=models.SET_NULL, null=True, related_name='pengumuman_dibuat')
    diperbarui_pada = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    dibaca_oleh = models.ManyToManyField(Personel, related_name='pengumuman_dibaca', blank=True)

    class Meta:
        db_table = 'pengumuman_pengumuman'
        ordering = ['-tanggal_publikasi']

    def __str__(self):
        return self.judul

    @property
    def status_tayang(self):
        if not self.is_active:
            return "Tidak Aktif"
        now = timezone.now()
        if self.periode_mulai and now < self.periode_mulai:
            return "Akan Tayang"
        if self.periode_selesai and now > self.periode_selesai:
            return "Selesai Tayang"
        return "Sedang Tayang"
