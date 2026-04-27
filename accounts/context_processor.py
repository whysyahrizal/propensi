from django.db.models import Q
from .models import MenuItem, Personel


def jumlah_verifikasi(request):
    """Menghitung jumlah antrean verifikasi untuk ditampilkan di dashboard"""
    if request.user.is_authenticated and (request.user.is_superadmin or request.user.is_operator):
        count = Personel.objects.filter(status_verifikasi='pending').count()
        return {'jumlah_pending_verifikasi': count}
    return {'jumlah_pending_verifikasi': 0}


def sidebar_menu_processor(request):
    if request.user.is_authenticated:
        role = request.user.role_obj

        if role:
            allowed_menus = role.menus.filter(is_active=True)
        else:
            allowed_menus = MenuItem.objects.none()

        allowed_menu_ids = set(allowed_menus.values_list('id', flat=True))

        menus = MenuItem.objects.filter(
            parent=None, 
            is_active=True
        ).filter(
            Q(id__in=allowed_menu_ids) | Q(submenus__id__in=allowed_menu_ids)
        ).distinct().prefetch_related('submenus').order_by('sort_order')
        
        return {
            'sidebar_menus': menus,
            'user_allowed_menu_ids': allowed_menu_ids, # Kirim ID untuk pengecekan di template
            'jumlah_pending_verifikasi': Personel.objects.filter(status_verifikasi='pending').count() if request.user.is_superadmin or request.user.is_operator else 0
        }
    return {}