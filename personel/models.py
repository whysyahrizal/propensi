from django.db import models

class Unit(models.Model):
    nama = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nama']

    def __str__(self):
        return self.nama


class Personel(models.Model):
    nama = models.CharField(max_length=150)
    nip = models.CharField(max_length=30, unique=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='personels')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nama']

    def __str__(self):
        return f"{self.nama} - {self.nip}"