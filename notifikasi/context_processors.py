from .models import Notifikasi

def notifikasi_unread_count(request):
    """
    Context processor untuk menyediakan jumlah notifikasi yang belum dibaca
    ke semua template (sebagai variabel `notif_unread_count`).
    """
    if request.user.is_authenticated:
        count = Notifikasi.objects.filter(user=request.user, is_read=False).count()
        return {'notif_unread_count': count}
    return {'notif_unread_count': 0}
