from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import os
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from .models import PengajuanCuti
from .forms import LeaveRequestForm

KUOTA_CUTI_TAHUNAN = 12


def get_kuota_info(user, year=None):
    """Menghitung total hari cuti yang sudah dipakai dan sisa kuota tahunan."""
    if year is None:
        year = timezone.now().year
    pengajuan = PengajuanCuti.objects.filter(
        personel=user,
        jenis_cuti='tahunan',
        status__in=['pending', 'approved'],
        tanggal_mulai__year=year,
    )
    hari_terpakai = sum(p.durasi_hari for p in pengajuan)
    sisa_hari = max(0, KUOTA_CUTI_TAHUNAN - hari_terpakai)
    return {
        'total_kuota': KUOTA_CUTI_TAHUNAN,
        'hari_terpakai': hari_terpakai,
        'sisa_hari': sisa_hari,
        'tahun': year,
    }


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    model = PengajuanCuti
    form_class = LeaveRequestForm
    template_name = 'manajemen_cuti/pengajuan_form.html'
    success_url = reverse_lazy('manajemen_cuti:riwayat')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_kuota_info(self.request.user))
        return ctx

    def form_valid(self, form):
        form.instance.personel = self.request.user
        # Auto-set satuan_kerja from user's satker if not explicitly set
        if not form.cleaned_data.get('satuan_kerja') and self.request.user.satker:
            form.instance.satuan_kerja = self.request.user.satker

        # pbi 033: validasi overlap
        overlap = PengajuanCuti.objects.filter(
            personel=self.request.user,
            status__in=['pending', 'approved']
        ).filter(
            Q(tanggal_mulai__range=(form.cleaned_data['tanggal_mulai'], form.cleaned_data['tanggal_selesai'])) |
            Q(tanggal_selesai__range=(form.cleaned_data['tanggal_mulai'], form.cleaned_data['tanggal_selesai'])) |
            Q(tanggal_mulai__lte=form.cleaned_data['tanggal_mulai'], tanggal_selesai__gte=form.cleaned_data['tanggal_selesai'])
        ).exists()

        if overlap:
            messages.error(self.request, "Anda sudah memiliki pengajuan cuti aktif pada periode tersebut.")
            return self.form_invalid(form)

        response = super().form_valid(form)

        # Flash message dengan info sisa kuota (hanya untuk cuti tahunan)
        if form.cleaned_data.get('jenis_cuti') == 'tahunan':
            kuota = get_kuota_info(self.request.user)
            sisa = kuota['sisa_hari']
            messages.success(
                self.request,
                f"Pengajuan cuti berhasil dikirim! Sisa jatah cuti tahunan Anda: {sisa} hari."
            )
        else:
            messages.success(self.request, "Pengajuan cuti berhasil dikirim.")

        # PBI-045, PBI-047: Kirim notifikasi ke pimpinan satker & superadmin
        from accounts.models import Personel
        from notifikasi.utils import kirim_notifikasi_massal
        
        penerima = Personel.objects.filter(is_active=True).filter(
            Q(role='superadmin') | Q(role='pimpinan', satker=form.instance.satuan_kerja)
        ).distinct()
        
        link = reverse_lazy('manajemen_cuti:detail', kwargs={'pk': form.instance.pk})
        
        kirim_notifikasi_massal(
            users=penerima,
            judul='Pengajuan Cuti Baru',
            pesan=f"{self.request.user.nama_lengkap} mengajukan {form.instance.get_jenis_cuti_display()} untuk periode {form.instance.tanggal_mulai} s/d {form.instance.tanggal_selesai}.",
            tipe='cuti',
            link=str(link)
        )

        return response

class LeaveRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = PengajuanCuti
    form_class = LeaveRequestForm
    template_name = 'manajemen_cuti/pengajuan_form.html'
    success_url = reverse_lazy('manajemen_cuti:riwayat')

    def get_queryset(self):
        # Only allow editing own pending requests
        return PengajuanCuti.objects.filter(personel=self.request.user, status='pending')

    def form_valid(self, form):
        # pbi 033: validasi overlap (exclude current instance)
        overlap = PengajuanCuti.objects.filter(
            personel=self.request.user,
            status__in=['pending', 'approved']
        ).exclude(pk=self.object.pk).filter(
            Q(tanggal_mulai__range=(form.cleaned_data['tanggal_mulai'], form.cleaned_data['tanggal_selesai'])) |
            Q(tanggal_selesai__range=(form.cleaned_data['tanggal_mulai'], form.cleaned_data['tanggal_selesai'])) |
            Q(tanggal_mulai__lte=form.cleaned_data['tanggal_mulai'], tanggal_selesai__gte=form.cleaned_data['tanggal_selesai'])
        ).exists()

        if overlap:
            messages.error(self.request, "Anda sudah memiliki pengajuan cuti aktif pada periode tersebut.")
            return self.form_invalid(form)

        messages.success(self.request, "Pengajuan cuti berhasil diperbarui.")
        return super().form_valid(form)

class LeaveRequestDeleteView(LoginRequiredMixin, DeleteView):
    model = PengajuanCuti
    success_url = reverse_lazy('manajemen_cuti:riwayat')

    def get_queryset(self):
        # Only allow deleting own pending requests
        return PengajuanCuti.objects.filter(personel=self.request.user, status='pending')

    def post(self, request, *args, **kwargs):
        messages.success(self.request, "Pengajuan cuti berhasil dihapus.")
        return super().post(request, *args, **kwargs)

class LeaveHistoryListView(LoginRequiredMixin, ListView):
    model = PengajuanCuti
    template_name = 'manajemen_cuti/riwayat_list.html'
    context_object_name = 'pengajuan_list'
    paginate_by = 10

    def get_queryset(self):
        return PengajuanCuti.objects.filter(personel=self.request.user).order_by('-dibuat_pada')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_kuota_info(self.request.user))
        return ctx

class LeaveDetailView(LoginRequiredMixin, DetailView):
    model = PengajuanCuti
    template_name = 'manajemen_cuti/pengajuan_detail.html'
    context_object_name = 'cuti'

    def _can_approve(self, request, cuti):
        """Check if current user can approve/reject this leave request."""
        user = request.user
        if user.role == 'superadmin':
            return True
        if user.role == 'pimpinan':
            # Must be in the same satuan kerja
            return user.satker is not None and user.satker == cuti.satuan_kerja
        return False

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_approve'] = self._can_approve(self.request, self.get_object())
        return ctx

    def post(self, request, *args, **kwargs):
        cuti = self.get_object()
        if not self._can_approve(request, cuti):
            messages.error(request, "Akses ditolak. Anda tidak berwenang menyetujui pengajuan dari satuan kerja ini.")
            return redirect('manajemen_cuti:detail', pk=cuti.pk)

        action = request.POST.get('action')
        catatan = request.POST.get('catatan', '').strip()

        if action in ('approve', 'reject'):
            if action == 'reject' and not catatan:
                messages.error(request, "Catatan penolakan wajib diisi.")
                return redirect('manajemen_cuti:detail', pk=cuti.pk)

            cuti.status = 'approved' if action == 'approve' else 'rejected'
            cuti.catatan_pimpinan = catatan
            cuti.disetujui_oleh = request.user
            cuti.disetujui_pada = timezone.now()
            cuti.save()
            messages.success(request, f"Pengajuan telah {'disetujui' if action == 'approve' else 'ditolak'}.")

            # PBI-045, PBI-047: Kirim notifikasi ke pemohon
            from notifikasi.utils import kirim_notifikasi
            link = reverse_lazy('manajemen_cuti:detail', kwargs={'pk': cuti.pk})
            status_text = 'Disetujui' if action == 'approve' else 'Ditolak'
            kirim_notifikasi(
                user=cuti.personel,
                judul=f"Pengajuan Cuti {status_text}",
                pesan=f"Pengajuan cuti Anda untuk periode {cuti.tanggal_mulai} s/d {cuti.tanggal_selesai} telah {status_text.lower()} oleh {request.user.nama_lengkap}.",
                tipe='cuti',
                link=str(link)
            )

        # pbi 036: final document upload for superadmin
        elif request.user.role == 'superadmin' and action == 'upload_final':
            file = request.FILES.get('surat_cuti_final')
            if not file:
                messages.error(request, "Silakan pilih file untuk diunggah.")
            else:
                # Validate file type
                allowed_types = ['application/pdf', 'application/msword',
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
                allowed_exts = ['.pdf', '.doc', '.docx']
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in allowed_exts or file.content_type not in allowed_types:
                    messages.error(request, f"Tipe file tidak diizinkan. Hanya PDF, DOC, atau DOCX ({ext}).")
                elif file.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.error(request, f"Ukuran file terlalu besar ({file.size // 1024 // 1024:.1f}MB). Maksimal 5MB.")
                else:
                    cuti.surat_cuti_final = file
                    cuti.save()
                    messages.success(request, f"Surat cuti final '{file.name}' berhasil diunggah.")

                    # PBI-045, PBI-047: Kirim notifikasi ke pemohon
                    from notifikasi.utils import kirim_notifikasi
                    link = reverse_lazy('manajemen_cuti:detail', kwargs={'pk': cuti.pk})
                    kirim_notifikasi(
                        user=cuti.personel,
                        judul="Surat Cuti Final Tersedia",
                        pesan="Surat cuti final Anda telah diterbitkan dan dapat diunduh sekarang.",
                        tipe='cuti',
                        link=str(link)
                    )

        return redirect('manajemen_cuti:detail', pk=cuti.pk)

class LeaveAdminListView(LoginRequiredMixin, ListView):
    model = PengajuanCuti
    template_name = 'manajemen_cuti/admin_list.html'
    context_object_name = 'pengajuan_list'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        if user.role not in ('pimpinan', 'operator', 'superadmin'):
            return PengajuanCuti.objects.none()

        qs = PengajuanCuti.objects.all().select_related('personel', 'satuan_kerja')

        # Pimpinan hanya melihat pengajuan dari satker-nya sendiri
        if user.role == 'pimpinan' and user.satker:
            qs = qs.filter(satuan_kerja=user.satker)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(personel__nama_lengkap__icontains=q) | Q(personel__nrp__icontains=q))
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        dari = self.request.GET.get('dari')
        if dari:
            qs = qs.filter(tanggal_mulai__gte=dari)

        sampai = self.request.GET.get('sampai')
        if sampai:
            qs = qs.filter(tanggal_selesai__lte=sampai)

        return qs.order_by('-dibuat_pada')
