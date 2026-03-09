from django.db import models
from django.conf import settings


class PengajuanCuti(models.Model):
    JENIS_CUTI_CHOICES = [
        ('tahunan', 'Cuti Tahunan'),
        ('sakit', 'Cuti Sakit'),
        ('alasan_penting', 'Cuti Alasan Penting'),
        ('besar', 'Cuti Besar'),
        ('di_luar_tanggungan', 'Cuti di Luar Tanggungan Negara'),
    ]

    STATUS_CHOICES = [
        ('menunggu', 'Menunggu Persetujuan'),
        ('disetujui', 'Disetujui'),
        ('ditolak', 'Ditolak'),
    ]

    personel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='pengajuan_cuti', verbose_name='Personel'
    )
    disetujui_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cuti_disetujui',
        verbose_name='Disetujui Oleh'
    )
    jenis_cuti = models.CharField(max_length=30, choices=JENIS_CUTI_CHOICES, verbose_name='Jenis Cuti')
    tanggal_mulai = models.DateField(verbose_name='Tanggal Mulai')
    tanggal_selesai = models.DateField(verbose_name='Tanggal Selesai')
    alasan = models.TextField(verbose_name='Alasan / Keterangan')
    dokumen_pendukung = models.FileField(
        upload_to='cuti/dokumen/', blank=True, null=True,
        verbose_name='Dokumen Pendukung (JPG/PNG/PDF)'
    )
    file_surat_resmi = models.FileField(
        upload_to='cuti/surat_resmi/', blank=True, null=True,
        verbose_name='Surat Cuti Resmi (upload SDM)'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='menunggu', verbose_name='Status')
    catatan_pimpinan = models.TextField(blank=True, verbose_name='Catatan Pimpinan')
    diajukan_pada = models.DateTimeField(auto_now_add=True, verbose_name='Diajukan Pada')
    diproses_pada = models.DateTimeField(null=True, blank=True, verbose_name='Diproses Pada')

    class Meta:
        verbose_name = 'Pengajuan Cuti'
        verbose_name_plural = 'Pengajuan Cuti'
        ordering = ['-diajukan_pada']

    def __str__(self):
        return f"{self.personel} — {self.get_jenis_cuti_display()} ({self.tanggal_mulai} s.d. {self.tanggal_selesai})"

    @property
    def jumlah_hari(self):
        delta = self.tanggal_selesai - self.tanggal_mulai
        return delta.days + 1
