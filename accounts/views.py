from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import cek_akses_menu
from .models import Personel, Satker, Role, MenuItem
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

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
        
        user_check = Personel.objects.filter(nrp=nrp).first()
        
        if not user_check:
            messages.error(request, 'Autentikasi gagal. Akun dengan NRP tersebut tidak terdaftar di dalam sistem.')
            return render(request, 'accounts/login.html')
            
        if user_check.status_verifikasi == 'pending':
            messages.warning(request, 'Akses ditolak. Akun Anda masih dalam proses verifikasi. Silakan hubungi Administrator untuk tindak lanjut.')
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=nrp, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Akses ditolak. Akun Anda telah dinonaktifkan. Silakan hubungi Administrator untuk informasi lebih lanjut.')
                return render(request, 'accounts/login.html')
            
            login(request, user)
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Autentikasi gagal. Password yang Anda masukkan tidak valid.')
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Anda berhasil keluar dari sistem.')
    return redirect('accounts:login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        email = request.POST.get('email', '').strip()
        no_hp = request.POST.get('no_hp', '').strip()
        jabatan = request.POST.get('jabatan', '').strip()
        pangkat = request.POST.get('pangkat', '')
        satker_id = request.POST.get('satker')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not all([nrp, nama, email, no_hp, jabatan, pangkat, satker_id, password1, password2]):
            messages.error(request, 'Seluruh kolom bertanda bintang (*) wajib diisi.')
        elif Personel.objects.filter(nrp=nrp).exists():
            messages.error(request, 'NRP sudah terdaftar di sistem.')
        elif password1 != password2:
            messages.error(request, 'Konfirmasi password tidak cocok.')
        elif len(password1) < 8:
            messages.error(request, 'Password minimal 8 karakter.')
        else:
            satker = Satker.objects.filter(pk=satker_id).first()
            user = Personel.objects.create_user(
                nrp=nrp, password=password1, nama_lengkap=nama,
                email=email, no_hp=no_hp, pangkat=pangkat,
                jabatan=jabatan, satker=satker,
                is_active=False, status_verifikasi='pending'
            )
            messages.success(request, 'Registrasi berhasil! Silakan tunggu verifikasi Administrator.')
            return redirect('accounts:login')
        
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

# MANAJEMEN PERSONEL
@cek_akses_menu('accounts:daftar_personel')
def daftar_personel_view(request):
    q = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    satker_filter = request.GET.get('satker', '').strip()
    status_filter = request.GET.get('status', '').strip()

    personel_list = Personel.objects.select_related('satker').order_by('nama_lengkap')

    if q:
        personel_list = personel_list.filter(Q(nama_lengkap__icontains=q) | Q(nrp__icontains=q))
    if role_filter:
        personel_list = personel_list.filter(role_obj_id=role_filter)
    if satker_filter:
        personel_list = personel_list.filter(satker_id=satker_filter)
    if status_filter == 'aktif':
        personel_list = personel_list.filter(is_active=True)
    elif status_filter == 'nonaktif':
        personel_list = personel_list.filter(is_active=False)

    paginator = Paginator(personel_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    role_list = Role.objects.all()
    satker_list = Satker.objects.all()

    base_queryset = Personel.objects.all()
    total_keseluruhan = base_queryset.count()
    total_aktif = base_queryset.filter(is_active=True).count()
    total_nonaktif = base_queryset.filter(is_active=False).count()

    return render(request, 'accounts/daftar_personel.html', {
        'page_obj': page_obj,
        'total_data_filter': paginator.count,
        'total_keseluruhan': total_keseluruhan,
        'total_aktif': total_aktif,
        'total_nonaktif': total_nonaktif,
        'q': q,
        'role_list': role_list,
        'satker_list': satker_list,
    })

@cek_akses_menu('accounts:daftar_personel')
def tambah_personel_view(request):
    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        email = request.POST.get('email', '').strip()
        pangkat = request.POST.get('pangkat', '')
        jabatan = request.POST.get('jabatan', '').strip()
        role_id = request.POST.get('role')
        satker_id = request.POST.get('satker')
        no_hp = request.POST.get('no_hp', '').strip()
        password = request.POST.get('password', '')

        if not nrp.isdigit() or len(nrp) != 8:
            messages.error(request, 'NRP harus berupa 8 digit angka.')
        elif Personel.objects.filter(nrp=nrp).exists():
            messages.error(request, 'NRP sudah terdaftar.')
        elif len(password) < 8:
            messages.error(request, 'Password minimal 8 karakter.')
        else:
            satker = Satker.objects.filter(pk=satker_id).first()
            role_obj = Role.objects.filter(pk=role_id).first()
            
            Personel.objects.create_user(
                nrp=nrp, password=password, nama_lengkap=nama,
                email=email, pangkat=pangkat, jabatan=jabatan,
                role_obj=role_obj, satker=satker, no_hp=no_hp
            )
            messages.success(request, f'Personel {nama} berhasil ditambahkan.')
            return redirect('accounts:daftar_personel')

    satker_list = Satker.objects.all()
    role_list = Role.objects.all()
    return render(request, 'accounts/form_personel.html', {
        'satker_list': satker_list,
        'role_list': role_list,
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'action': 'tambah',
        'form_data': request.POST if request.method == 'POST' else {}
    })

@cek_akses_menu('accounts:daftar_personel')
def edit_personel_view(request, pk):
    personel = get_object_or_404(Personel, pk=pk)
    
    if request.method == 'POST':
        personel.nama_lengkap = request.POST.get('nama_lengkap', '').strip()
        personel.email = request.POST.get('email', '').strip()
        personel.pangkat = request.POST.get('pangkat', '')
        personel.jabatan = request.POST.get('jabatan', '').strip()
        personel.no_hp = request.POST.get('no_hp', '').strip()
        
        satker_id = request.POST.get('satker')
        role_id = request.POST.get('role')
        personel.satker = Satker.objects.filter(pk=satker_id).first()
        if role_id:
            personel.role_obj = Role.objects.filter(pk=role_id).first()
        
        new_password = request.POST.get('password', '').strip()
        if new_password:
            if len(new_password) < 8:
                messages.error(request, 'Password baru minimal 8 karakter.')
                return render(request, 'accounts/form_personel.html', {
                    'personel': personel, 'action': 'edit', 
                    'satker_list': Satker.objects.all(), 'role_list': Role.objects.all()
                })
            personel.set_password(new_password)
            
        personel.save()
        messages.success(request, f'Data {personel.nama_lengkap} berhasil diperbarui.')
        return redirect('accounts:daftar_personel')

    return render(request, 'accounts/form_personel.html', {
        'personel': personel,
        'satker_list': Satker.objects.all(),
        'role_list': Role.objects.all(),
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'action': 'edit',
    })

@cek_akses_menu('accounts:daftar_personel')
def hapus_personel_view(request, pk):
    personel = get_object_or_404(Personel, pk=pk)
    
    if request.method == 'POST':
        alasan = request.POST.get('alasan', 'Tidak ada alasan spesifik')
        
        personel.is_active = False
        personel.tanggal_nonaktif = timezone.now()
        personel.alasan_nonaktif = alasan
        personel.save()
        
        messages.success(request, f'Akun {personel.nama_lengkap} telah dinonaktifkan.')
        return redirect('accounts:detail_personel', pk=personel.pk)

    return render(request, 'accounts/konfirmasi_hapus.html', {'personel': personel})

@cek_akses_menu('accounts:daftar_personel')
def detail_personel_view(request, pk):
    personel = get_object_or_404(Personel, pk=pk)
    return render(request, 'accounts/detail_personel.html', {
        'personel': personel,
    })

@cek_akses_menu('accounts:daftar_personel')
def reaktivasi_personel_view(request, pk):
    personel = get_object_or_404(Personel, pk=pk)
    if request.method == 'POST':
        nama = personel.nama_lengkap
        personel.is_active = True 
        personel.save()
        messages.success(request, f'Personel {nama} berhasil direaktivasi.')
        return redirect('accounts:daftar_personel')

    return render(request, 'accounts/konfirmasi_reaktivasi.html', {'personel': personel})

@cek_akses_menu('accounts:daftar_personel')
def daftar_verifikasi_view(request):
    if not (request.user.is_superadmin or request.user.is_operator):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')
        
    antrean_list = Personel.objects.filter(status_verifikasi='pending').order_by('-id')
    return render(request, 'accounts/verifikasi/daftar_antrean.html', {'antrean_list': antrean_list})

@cek_akses_menu('accounts:daftar_personel')
def detail_verifikasi_view(request, pk):
    if not (request.user.is_superadmin or request.user.is_operator):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')
    personel = get_object_or_404(Personel, pk=pk, status_verifikasi='pending')
    return render(request, 'accounts/verifikasi/detail_verifikasi.html', {'personel': personel})

@cek_akses_menu('accounts:daftar_personel')
def proses_verifikasi_view(request, pk, action):
    if not (request.user.is_superadmin or request.user.is_operator):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')
        
    personel = get_object_or_404(Personel, pk=pk)
    
    if request.method == 'POST':
        if action == 'approve':
            personel.is_active = True
            personel.status_verifikasi = 'approved'
            personel.save()
            messages.success(request, f'Akun {personel.nama_lengkap} disetujui.')
        elif action == 'reject':
            personel.delete()
            messages.success(request, f'Pendaftaran {personel.nama_lengkap} ditolak.')
            
    return redirect('accounts:daftar_verifikasi')

# MANAJEMEN ROLE
@cek_akses_menu('accounts:daftar_role')
def daftar_role(request):
    role_list = Role.objects.all().prefetch_related('menus')
    return render(request, 'accounts/role/daftar_role.html', {
        'role_list': role_list,
        'total': role_list.count(),
    })

@cek_akses_menu('accounts:daftar_role')
def detail_role(request, pk):
    role = get_object_or_404(Role, pk=pk)
    pengguna_list = role.personel_set.filter(is_active=True).select_related('satker')
    return render(request, 'accounts/role/detail_role.html', {
        'role': role,
        'pengguna_list': pengguna_list,
    })

@cek_akses_menu('accounts:daftar_role')
def tambah_role(request):
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip().lower()
        display_label = request.POST.get('display_label', '').strip()
        deskripsi = request.POST.get('deskripsi', '').strip()

        if not nama or not display_label:
            messages.error(request, 'Role Name dan Display Label wajib diisi.')
        elif Role.objects.filter(nama=nama).exists():
            messages.error(request, f'Role "{nama}" sudah digunakan.')
        else:
            role = Role.objects.create(
                nama=nama, 
                display_label=display_label, 
                deskripsi=deskripsi
            )
            messages.success(request, f'Role "{role.display_label}" berhasil ditambahkan.')
            return redirect('accounts:daftar_role')

    return render(request, 'accounts/role/form_role.html', {'action': 'tambah'})

@cek_akses_menu('accounts:daftar_role')
def edit_role(request, pk):
    role = get_object_or_404(Role, pk=pk)

    if request.method == 'POST':
        role.display_label = request.POST.get('display_label', '').strip()
        role.deskripsi = request.POST.get('deskripsi', '').strip()
        role.save()
        messages.success(request, f'Role "{role.display_label}" berhasil diperbarui.')
        return redirect('accounts:daftar_role')

    return render(request, 'accounts/role/form_role.html', {
        'action': 'edit',
        'role': role,
    })

@cek_akses_menu('accounts:daftar_role')
def hapus_role(request, pk):
    role = get_object_or_404(Role, pk=pk)
    jumlah_pengguna = role.personel_set.filter(is_active=True).count()

    if request.method == 'POST':
        if jumlah_pengguna > 0:
            messages.error(request, f'Role tidak dapat dihapus karena masih digunakan oleh {jumlah_pengguna} pengguna.')
            return redirect('accounts:daftar_role')
            
        label = role.display_label or role.nama
        role.delete()
        messages.success(request, f'Role "{label}" berhasil dihapus.')
        return redirect('accounts:daftar_role')

    return render(request, 'accounts/role/konfirmasi_hapus_role.html', {
        'role': role,
        'jumlah_pengguna': jumlah_pengguna,
    })

@cek_akses_menu('accounts:daftar_role')
def kelola_akses_menu(request, pk):
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        menu_ids = request.POST.getlist('menus')
        role.menus.set(menu_ids)
        messages.success(request, f'Akses menu untuk Role "{role.display_label or role.nama}" berhasil diperbarui.')
        return redirect('accounts:daftar_role')

    semua_menu = MenuItem.objects.filter(is_active=True).order_by('sort_order')
    menu_aktif_ids = role.menus.values_list('id', flat=True)

    return render(request, 'accounts/role/kelola_akses.html', {
        'role': role,
        'semua_menu': semua_menu,
        'menu_aktif_ids': menu_aktif_ids,
    })


# MANAJEMEN MENU
@cek_akses_menu('accounts:daftar_menu')
def daftar_menu(request):
    menus = MenuItem.objects.all().order_by('sort_order')
    return render(request, 'accounts/menu/daftar_menu.html', {'menus': menus})

@cek_akses_menu('accounts:daftar_menu')
def toggle_status_menu(request, pk):
    menu = get_object_or_404(MenuItem, pk=pk)

    if request.method == 'POST':
        menu.is_active = not menu.is_active
        menu.save()
        
        status = "diaktifkan" if menu.is_active else "dinonaktifkan"
        messages.success(request, f'Menu "{menu.label}" berhasil {status}.')
        
    return redirect('accounts:daftar_menu')