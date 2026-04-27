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
        # Pengumuman yang belum dibaca (jangan tampilkan untuk pembuatnya)
        unread = active_pengumuman.exclude(dibaca_oleh=request.user).exclude(dibuat_oleh=request.user)
        
        # Pengingat H-1 Pelaksanaan (jangan tampilkan untuk pembuatnya)
        tomorrow = (now + timedelta(days=1)).date()
        reminders = active_pengumuman.filter(tanggal_pelaksanaan=tomorrow).exclude(dibuat_oleh=request.user)
        
        return {
            'pengumuman_baru_count': unread.count(),
            'pengumuman_unread_list': unread.order_by('-tanggal_publikasi')[:5],
            'pengumuman_reminder_list': reminders.order_by('-tanggal_publikasi')[:5],
            'pengumuman_total_notif': unread.count() + reminders.count(),
        }
    return {}
