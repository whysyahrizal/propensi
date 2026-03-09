from .models import Notifikasi


def notifikasi_count(request):
    """Inject jumlah notifikasi belum dibaca ke semua template."""
    if request.user.is_authenticated:
        count = Notifikasi.objects.filter(penerima=request.user, is_read=False).count()
        recent = Notifikasi.objects.filter(penerima=request.user).order_by('-dibuat_pada')[:5]
        return {'notif_count': count, 'notif_recent': recent}
    return {'notif_count': 0, 'notif_recent': []}
