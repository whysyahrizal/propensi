from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personel, Satker


def redirect_root(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=nrp, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'NRP atau password salah. Silakan coba lagi.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Anda berhasil keluar dari sistem.')
    return redirect('accounts:login')


def register_view(request):
    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        satker_id = request.POST.get('satker')
        pangkat = request.POST.get('pangkat', '')

        if Personel.objects.filter(nrp=nrp).exists():
            messages.error(request, 'NRP sudah terdaftar di sistem.')
        elif password1 != password2:
            messages.error(request, 'Konfirmasi password tidak cocok.')
        elif len(password1) < 8:
            messages.error(request, 'Password minimal 8 karakter.')
        else:
            satker = Satker.objects.filter(pk=satker_id).first() if satker_id else None
            user = Personel.objects.create_user(
                nrp=nrp,
                password=password1,
                nama_lengkap=nama,
                pangkat=pangkat,
                satker=satker,
            )
            login(request, user)
            messages.success(request, f'Selamat datang, {user.nama_lengkap}!')
            return redirect('dashboard:index')

    satker_list = Satker.objects.all()
    pangkat_choices = Personel.PANGKAT_CHOICES
    return render(request, 'accounts/register.html', {
        'satker_list': satker_list,
        'pangkat_choices': pangkat_choices,
    })


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.nama_lengkap = request.POST.get('nama_lengkap', user.nama_lengkap)
        user.email = request.POST.get('email', user.email)
        user.no_hp = request.POST.get('no_hp', user.no_hp)
        user.jabatan = request.POST.get('jabatan', user.jabatan)
        if 'foto' in request.FILES:
            user.foto = request.FILES['foto']
        user.save()
        messages.success(request, 'Profil berhasil diperbarui.')
        return redirect('accounts:profil')

    return render(request, 'accounts/profil.html', {'user': request.user})


@login_required
def daftar_personel_view(request):
    if request.user.role not in ('superadmin', 'operator'):
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('dashboard:index')

    q = request.GET.get('q', '').strip()
    personel_list = Personel.objects.select_related('satker').order_by('nama_lengkap')
    if q:
        personel_list = personel_list.filter(
            nama_lengkap__icontains=q
        ) | personel_list.filter(nrp__icontains=q)

    return render(request, 'accounts/daftar_personel.html', {
        'personel_list': personel_list,
        'q': q,
    })


@login_required
def tambah_personel_view(request):
    if request.user.role != 'superadmin':
        messages.error(request, 'Hanya Superadmin yang dapat menambah personel.')
        return redirect('accounts:daftar_personel')

    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        pangkat = request.POST.get('pangkat', '')
        jabatan = request.POST.get('jabatan', '')
        role = request.POST.get('role', 'personel')
        satker_id = request.POST.get('satker')
        email = request.POST.get('email', '')
        no_hp = request.POST.get('no_hp', '')

        if Personel.objects.filter(nrp=nrp).exists():
            messages.error(request, 'NRP sudah terdaftar.')
        else:
            satker = Satker.objects.filter(pk=satker_id).first() if satker_id else None
            Personel.objects.create_user(
                nrp=nrp, password='siraga2026',  # default password, wajib diganti
                nama_lengkap=nama, pangkat=pangkat, jabatan=jabatan,
                role=role, satker=satker, email=email, no_hp=no_hp,
            )
            messages.success(request, f'Personel {nama} berhasil ditambahkan. Password default: siraga2026')
            return redirect('accounts:daftar_personel')

    satker_list = Satker.objects.all()
    return render(request, 'accounts/form_personel.html', {
        'satker_list': satker_list,
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'role_choices': Personel.ROLE_CHOICES,
        'action': 'tambah',
    })


@login_required
def edit_personel_view(request, pk):
    if request.user.role != 'superadmin':
        messages.error(request, 'Hanya Superadmin yang dapat mengedit personel.')
        return redirect('accounts:daftar_personel')

    personel = get_object_or_404(Personel, pk=pk)
    if request.method == 'POST':
        personel.nama_lengkap = request.POST.get('nama_lengkap', personel.nama_lengkap)
        personel.pangkat = request.POST.get('pangkat', personel.pangkat)
        personel.jabatan = request.POST.get('jabatan', personel.jabatan)
        personel.role = request.POST.get('role', personel.role)
        personel.email = request.POST.get('email', personel.email)
        personel.no_hp = request.POST.get('no_hp', personel.no_hp)
        satker_id = request.POST.get('satker')
        personel.satker = Satker.objects.filter(pk=satker_id).first() if satker_id else None
        personel.save()
        messages.success(request, 'Data personel berhasil diperbarui.')
        return redirect('accounts:daftar_personel')

    satker_list = Satker.objects.all()
    return render(request, 'accounts/form_personel.html', {
        'personel': personel,
        'satker_list': satker_list,
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'role_choices': Personel.ROLE_CHOICES,
        'action': 'edit',
    })


@login_required
def hapus_personel_view(request, pk):
    if request.user.role != 'superadmin':
        messages.error(request, 'Hanya Superadmin yang dapat menghapus personel.')
        return redirect('accounts:daftar_personel')

    personel = get_object_or_404(Personel, pk=pk)
    if request.method == 'POST':
        nama = personel.nama_lengkap
        personel.delete()
        messages.success(request, f'Personel {nama} berhasil dihapus.')
        return redirect('accounts:daftar_personel')

    return render(request, 'accounts/konfirmasi_hapus.html', {'personel': personel})
