from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q

from .models import PengajuanCuti
from .forms import LeaveRequestForm

class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    model = PengajuanCuti
    form_class = LeaveRequestForm
    template_name = 'manajemen_cuti/pengajuan_form.html'
    success_url = reverse_lazy('manajemen_cuti:riwayat')

    def form_valid(self, form):
        form.instance.personel = self.request.user
        
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

        messages.success(self.request, "Pengajuan cuti berhasil dikirim.")
        return super().form_valid(form)

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

class LeaveDetailView(LoginRequiredMixin, DetailView):
    model = PengajuanCuti
    template_name = 'manajemen_cuti/pengajuan_detail.html'
    context_object_name = 'cuti'

    def post(self, request, *args, **kwargs):
        cuti = self.get_object()
        if request.user.role not in ('pimpinan', 'superadmin'):
            messages.error(request, "Akses ditolak.")
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
            
        # pbi 036: final document upload for superadmin
        elif request.user.role == 'superadmin' and action == 'upload_final':
            file = request.FILES.get('surat_cuti_final')
            if file:
                cuti.surat_cuti_final = file
                cuti.save()
                messages.success(request, "Surat cuti final berhasil diunggah.")
            else:
                messages.error(request, "Silakan pilih file untuk diunggah.")
            
        return redirect('manajemen_cuti:detail', pk=cuti.pk)

class LeaveAdminListView(LoginRequiredMixin, ListView):
    model = PengajuanCuti
    template_name = 'manajemen_cuti/admin_list.html'
    context_object_name = 'pengajuan_list'
    paginate_by = 15

    def get_queryset(self):
        if self.request.user.role not in ('pimpinan', 'operator', 'superadmin'):
            return PengajuanCuti.objects.none()
        qs = PengajuanCuti.objects.all().select_related('personel')
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
