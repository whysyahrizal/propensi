from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def cek_akses_menu(menu_path):
    """
    Dekorator untuk mengecek apakah Role pengguna memiliki akses ke URL tertentu.
    Parameter menu_path adalah nama URL (contoh: 'accounts:daftar_role').
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if request.user.is_superadmin:
                return view_func(request, *args, **kwargs)

            if request.user.role_obj:
                punya_akses = request.user.role_obj.menus.filter(
                    path=menu_path, 
                    is_active=True
                ).exists()
                
                if punya_akses:
                    return view_func(request, *args, **kwargs)

            messages.error(request, 'Akses ditolak. Anda tidak memiliki izin untuk membuka halaman tersebut.')
            return redirect('dashboard:index')
            
        return _wrapped_view
    return decorator