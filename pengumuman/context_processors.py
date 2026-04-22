from django.utils import timezone
from datetime import timedelta
from django.db import models
from .models import Pengumuman

def pengumuman_aktif(request):
    if request.user.is_authenticated:
        now = timezone.now()
        active_pengumuman = Pengumuman.objects.filter(is_active=True).filter(
            models.Q(periode_mulai__isnull=True) | models.Q(periode_mulai__lte=now)
        ).filter(
            models.Q(periode_selesai__isnull=True) | models.Q(periode_selesai__gte=now)
        )
        count = active_pengumuman.exclude(dibaca_oleh=request.user).count()
        return {'pengumuman_baru_count': count}
    return {}
