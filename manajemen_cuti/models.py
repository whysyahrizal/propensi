from django.db import models
from django.conf import settings
from django.utils import timezone
import os

def lampiran_cuti_path(instance, filename):
    return f'cuti/lampiran/{instance.personel.nrp}/{filename}'

def surat_final_path(instance, filename):
    return f'cuti/final/{instance.personel.nrp}/{filename}'

class PengajuanCuti(models.Model):
    JENIS_CUTI_CHOICES = [
        ('tahunan', 'Cuti Tahunan'),
        ('sakit', 'Cuti Sakit'),
        ('bersalin', 'Cuti Bersalin'),
        ('alasan_penting', 'Cuti Alasan Penting'),
        ('besar', 'Cuti Besar'),
        ('luar_tanggungan', 'Cuti di Luar Tanggungan Negara'),
        ('izin', 'Izin'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    personel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='pengajuan_cuti', verbose_name='Personel'
    )
    jenis_cuti = models.CharField(max_length=20, choices=JENIS_CUTI_CHOICES, verbose_name='Jenis Cuti')
    tanggal_mulai = models.DateField(verbose_name='Tanggal Mulai')
    tanggal_selesai = models.DateField(verbose_name='Tanggal Selesai')
    alasan = models.TextField(verbose_name='Alasan Cuti')
    
    # PBI-033: Attachment for request
    lampiran = models.FileField(
        upload_to=lampiran_cuti_path, blank=True, null=True, 
        verbose_name='Dokumen Pendukung'
    )
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    
    # PBI-034: Approval data
    catatan_pimpinan = models.TextField(blank=True, verbose_name='Catatan Pimpinan')
    disetujui_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approval_cuti', verbose_name='Diputuskan Oleh'
    )
    disetujui_pada = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Keputusan')
    
    # PBI-036: Final Document from Superadmin
    surat_cuti_final = models.FileField(
        upload_to=surat_final_path, blank=True, null=True,
        verbose_name='Surat Cuti Final'
    )
    
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pengajuan Cuti'
        verbose_name_plural = 'Pengajuan Cuti'
        ordering = ['-dibuat_pada']

    def __str__(self):
        return f"Cuti {self.get_jenis_cuti_display()} - {self.personel} ({self.tanggal_mulai} s/d {self.tanggal_selesai})"

    @property
    def durasi_hari(self):
        return (self.tanggal_selesai - self.tanggal_mulai).days + 1
