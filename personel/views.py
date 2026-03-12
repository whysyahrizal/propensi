from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy

from .models import Personel, Unit
from .forms import PersonelForm


class PersonelListView(ListView):
    model = Personel
    template_name = 'personel/personel_list.html'
    context_object_name = 'personels'
    paginate_by = 5

    def get_queryset(self):
        queryset = Personel.objects.select_related('unit').filter(is_active=True)

        q = self.request.GET.get('q', '').strip()
        unit_id = self.request.GET.get('unit', '').strip()

        if q:
            queryset = queryset.filter(
                Q(nama__icontains=q) | Q(nip__icontains=q)
            )

        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)

        return queryset.order_by('nama')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = Unit.objects.all()
        context['q'] = self.request.GET.get('q', '').strip()
        context['selected_unit'] = self.request.GET.get('unit', '').strip()
        context['total_data'] = self.get_queryset().count()
        context['active_nav'] = 'personel'
        return context


class PersonelDetailView(DetailView):
    model = Personel
    template_name = 'personel/personel_detail.html'
    context_object_name = 'personel'

    def get_queryset(self):
        return Personel.objects.select_related('unit').filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'personel'
        return context


class PersonelCreateView(CreateView):
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


class PersonelUpdateView(UpdateView):
    model = Personel
    form_class = PersonelForm
    template_name = 'personel/personel_form.html'
    success_url = reverse_lazy('personel_list')
    context_object_name = 'personel'

    def get_queryset(self):
        return Personel.objects.filter(is_active=True)

    def form_valid(self, form):
        messages.success(self.request, 'Data personel berhasil diperbarui.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Gagal memperbarui data personel. Cek kembali input.')
        return super().form_invalid(form)


class PersonelDeleteView(View):
    def post(self, request, pk):
        personel = get_object_or_404(Personel, pk=pk, is_active=True)
        personel.is_active = False
        personel.save()
        messages.success(request, 'Personel berhasil dinonaktifkan.')
        return redirect('personel_list')