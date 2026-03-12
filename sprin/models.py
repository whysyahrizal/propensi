import uuid
from django.db import models
from django.utils import timezone

class Sprin(models.Model):
    STATUS_CHOICES = [
        ('Menunggu Persetujuan', 'Menunggu Persetujuan'),
        ('Disetujui', 'Disetujui'),
        ('Ditolak', 'Ditolak'),
    ]

    id_sprin = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Data Lokasi untuk referensi
    location_name = models.CharField(max_length=255)
    # latitude = models.DecimalField(max_digits=12, decimal_places=9, null=True, blank=True)
    # longitude = models.DecimalField(max_digits=12, decimal_places=9, null=True, blank=True)
    # radius_meter = models.IntegerField(default=100)
    
    # Relasi ke modul Personel
    created_by = models.ForeignKey('personel.Personel', on_delete=models.SET_NULL, null=True, related_name='sprin_dibuat')
    approved_by = models.ForeignKey('personel.Personel', on_delete=models.SET_NULL, null=True, blank=True, related_name='sprin_pimpinan')
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Menunggu Persetujuan')
    rejection_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    file_surat = models.FileField(upload_to='sprin_pdf/', null=True, blank=True)
    
    @property
    def dapat_disetujui(self):
        return self.status == 'Menunggu Persetujuan'

    @property
    def sudah_disetujui(self):
        return self.status == 'Disetujui'
    
    @property
    def is_active(self):
        """Menghitung status sprin apakah aktif atau tidak"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def __str__(self):
        return f"{self.operation_name} ({self.id_sprin})"

class PersonelSprin(models.Model):
    """Tabel junction untuk daftar personel di satu Sprin"""
    sprin = models.ForeignKey(Sprin, on_delete=models.CASCADE, related_name='daftar_personel')
    personel = models.ForeignKey('personel.Personel', on_delete=models.CASCADE, related_name='penugasan_sprin')

    class Meta:
        unique_together = ('sprin', 'personel')