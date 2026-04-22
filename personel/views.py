from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy

from .models import Personel, Unit
from .forms import PersonelForm


class PersonelListView(LoginRequiredMixin, ListView):
    model = Personel
    template_name = 'personel/personel_list.html'
    context_object_name = 'personels'
    paginate_by = 5

    def get_queryset(self):
        queryset = Personel.objects.select_related('unit').all()

        q = self.request.GET.get('q', '').strip()
        unit_id = self.request.GET.get('unit', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            queryset = queryset.filter(
                Q(nama__icontains=q) | Q(nip__icontains=q)
            )

        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)

        if status == 'aktif':
            queryset = queryset.filter(is_active=True)
        elif status == 'nonaktif':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('-is_active', 'nama')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = Personel.objects.all()
        
        context['units'] = Unit.objects.all()
        context['q'] = self.request.GET.get('q', '').strip()
        context['selected_unit'] = self.request.GET.get('unit', '').strip()
        context['selected_status'] = self.request.GET.get('status', '').strip()
        
        context['total_data'] = self.get_queryset().count()
        context['total_aktif'] = base_queryset.filter(is_active=True).count()
        context['total_nonaktif'] = base_queryset.filter(is_active=False).count()
        context['active_nav'] = 'personel'
        
        return context


class PersonelDetailView(LoginRequiredMixin, DetailView):
    model = Personel
    template_name = 'personel/personel_detail.html'
    context_object_name = 'personel'

    def get_queryset(self):
        return Personel.objects.select_related('unit').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'personel'
        return context


class PersonelCreateView(LoginRequiredMixin, CreateView):
    model = Personel
    form_class = PersonelForm
    template_name = 'personel/personel_form.html'
    success_url = reverse_lazy('personel_list')

    def form_valid(self, form):
        messages.success(self.request, 'Personel berhasil ditambahkan.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Gagal menambahkan personel. Cek kembali input.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'personel'
        return context


class PersonelUpdateView(LoginRequiredMixin, UpdateView):
    model = Personel
    form_class = PersonelForm
    template_name = 'personel/personel_form.html'
    success_url = reverse_lazy('personel_list')
    context_object_name = 'personel'

    def get_queryset(self):
        return Personel.objects.all()

    def form_valid(self, form):
        messages.success(self.request, 'Data personel berhasil diperbarui.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Gagal memperbarui data personel. Cek kembali input.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'personel'
        return context


class PersonelDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        personel = get_object_or_404(Personel, pk=pk)
        if personel.is_active:
            personel.is_active = False
            messages.success(request, 'Personel berhasil dinonaktifkan.')
        else:
            personel.is_active = True
            messages.success(request, 'Personel berhasil diaktifkan kembali.')
        
        personel.save()
        return redirect('personel_list')