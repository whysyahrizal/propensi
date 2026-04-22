from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Notifikasi


# PBI-045 — View All Notifikasi
@login_required
def daftar_notifikasi(request):
    """Tampilkan daftar notifikasi milik user yang sedang login."""
    filter_read = request.GET.get('filter', 'semua')  # semua | belum_dibaca | sudah_dibaca

    qs = Notifikasi.objects.filter(user=request.user)
    if filter_read == 'belum_dibaca':
        qs = qs.filter(is_read=False)
    elif filter_read == 'sudah_dibaca':
        qs = qs.filter(is_read=True)

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    total_unread = Notifikasi.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'notifikasi/daftar_notifikasi.html', {
        'page_obj': page_obj,
        'filter_read': filter_read,
        'total_unread': total_unread,
        'active_nav': 'notifikasi',
    })


# PBI-046 — View Detail Notifikasi
@login_required
def detail_notifikasi(request, pk):
    """Tampilkan detail notifikasi; otomatis tandai sebagai dibaca."""
    notif = get_object_or_404(Notifikasi, pk=pk)

    # Pastikan notifikasi milik user yang sedang login
    if notif.user != request.user:
        messages.error(request, 'Anda tidak memiliki akses ke notifikasi ini.')
        return redirect('notifikasi:daftar')

    # Auto mark-read saat detail dibuka (PBI-046)
    notif.tandai_dibaca()

    return render(request, 'notifikasi/detail_notifikasi.html', {
        'notif': notif,
        'active_nav': 'notifikasi',
    })


# PBI-046 — Bulk mark-read
@login_required
def tandai_semua_dibaca(request):
    """Tandai semua notifikasi user sebagai sudah dibaca."""
    if request.method == 'POST':
        from django.utils import timezone
        Notifikasi.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            dibaca_pada=timezone.now(),
        )
        messages.success(request, 'Semua notifikasi telah ditandai sebagai dibaca.')
    return redirect('notifikasi:daftar')

@login_required
def hapus_notifikasi(request, pk):
    """Hapus satu notifikasi."""
    if request.method == 'POST':
        notif = get_object_or_404(Notifikasi, pk=pk)
        if notif.user == request.user:
            notif.delete()
            messages.success(request, 'Notifikasi berhasil dihapus.')
        else:
            messages.error(request, 'Anda tidak berhak menghapus notifikasi ini.')
    return redirect('notifikasi:daftar')


@login_required
def hapus_semua_notifikasi(request):
    """Hapus seluruh notifikasi milik user."""
    if request.method == 'POST':
        Notifikasi.objects.filter(user=request.user).delete()
        messages.success(request, 'Seluruh notifikasi berhasil dihapus.')
    return redirect('notifikasi:daftar')
