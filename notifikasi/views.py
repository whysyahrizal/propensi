from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notifikasi


@login_required
def daftar_notifikasi(request):
    notifikasi_list = Notifikasi.objects.filter(penerima=request.user)
    return render(request, 'notifikasi/daftar.html', {'notifikasi_list': notifikasi_list})


@login_required
def tandai_baca(request, pk):
    notif = get_object_or_404(Notifikasi, pk=pk, penerima=request.user)
    notif.is_read = True
    notif.save()
    if notif.url_ref:
        return redirect(notif.url_ref)
    return redirect('notifikasi:daftar')


@login_required
def baca_semua(request):
    Notifikasi.objects.filter(penerima=request.user, is_read=False).update(is_read=True)
    return redirect('notifikasi:daftar')
