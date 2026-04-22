from .models import Personel

def jumlah_verifikasi(request):
    if request.user.is_authenticated and (request.user.is_superadmin or request.user.is_operator):
        count = Personel.objects.filter(status_verifikasi='pending').count()
        return {'jumlah_pending_verifikasi': count}
    return {'jumlah_pending_verifikasi': 0}