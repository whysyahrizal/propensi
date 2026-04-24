from django.conf import settings
from django.db import models
from django.utils import timezone

class Presensi(models.Model):
    TYPE_CHOICES = [
        ('Office Hour', 'Office Hour'),
        ('Dinas', 'Dinas'),
        ('Izin', 'Izin'),
    ]
    
    personel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Check-in Data
    checkin_time = models.TimeField(null=True, blank=True)
    checkin_photo = models.ImageField(upload_to='presensi/foto_masuk/', null=True, blank=True)
    
    # Check-out Data
    checkout_time = models.TimeField(null=True, blank=True)
    checkout_photo = models.ImageField(upload_to='presensi/foto_keluar/', null=True, blank=True)
    
    # Dokumen Izin / Dinas
    supporting_document = models.FileField(upload_to='presensi/dokumen/', null=True, blank=True)
    izin_detail = models.CharField(max_length=100, blank=True, null=True) #SAKIT/CUTI
    
    status = models.CharField(max_length=20, default='Alfa')

    class Meta:
        unique_together = ('personel', 'date')
