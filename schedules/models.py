from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from locations.models import Location


class ShiftSchedule(models.Model):
    SHIFT_PAGI = 'pagi'
    SHIFT_SIANG = 'siang'
    SHIFT_MALAM = 'malam'

    SHIFT_CHOICES = [
        (SHIFT_PAGI, 'Pagi'),
        (SHIFT_SIANG, 'Siang'),
        (SHIFT_MALAM, 'Malam'),
    ]

    date = models.DateField(verbose_name='Tanggal Jadwal')
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES, verbose_name='Jenis Shift')
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='schedules',
        verbose_name='Lokasi Penugasan',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedules_created',
        verbose_name='Dibuat Oleh',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jadwal Shift'
        verbose_name_plural = 'Jadwal Shift'
        ordering = ['date', 'shift_type', 'location__name']
        unique_together = ('date', 'shift_type', 'location')
        # Transitional: reuse existing dashboard tables.
        db_table = 'dashboard_shiftschedule'

    def __str__(self):
        return f"{self.date} - {self.get_shift_type_display()} - {self.location.name}"

    @property
    def personnel_count(self):
        return self.personnel_assignments.count()

    @property
    def is_historical(self):
        return self.date < timezone.localdate()

    def get_start_end(self):
        if self.shift_type == self.SHIFT_PAGI:
            start_t, end_t = time(7, 0), time(15, 0)
            date_end = self.date
        elif self.shift_type == self.SHIFT_SIANG:
            start_t, end_t = time(15, 0), time(23, 0)
            date_end = self.date
        else:
            start_t, end_t = time(23, 0), time(7, 0)
            date_end = self.date + timedelta(days=1)

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(self.date, start_t), tz)
        end_dt = timezone.make_aware(datetime.combine(date_end, end_t), tz)
        return start_dt, end_dt


class ShiftSchedulePersonnel(models.Model):
    schedule = models.ForeignKey(
        ShiftSchedule,
        on_delete=models.CASCADE,
        related_name='personnel_assignments',
        verbose_name='Jadwal',
    )
    personel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_shifts',
        verbose_name='Personel',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Personel Jadwal Shift'
        verbose_name_plural = 'Personel Jadwal Shift'
        unique_together = ('schedule', 'personel')
        ordering = ['personel__nama_lengkap']
        # Transitional: reuse existing dashboard tables.
        db_table = 'dashboard_shiftschedulepersonnel'

    def __str__(self):
        return f"{self.personel.nama_lengkap} @ {self.schedule}"
