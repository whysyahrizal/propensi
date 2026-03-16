from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Location
from .forms import LocationForm


def _check_sprin_linked(location):
    """Safely check whether this location's coordinates match an active Sprin."""
    try:
        from sprin.models import Sprin
        return Sprin.objects.filter(
            status='aktif',
            lat_lokasi=location.latitude,
            lon_lokasi=location.longitude,
        ).exists()
    except Exception:
        return False


@login_required
def location_list(request):
    qs = Location.objects.all()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(name__icontains=search)

    status_filter = request.GET.get('status', '')
    if status_filter == 'aktif':
        qs = qs.filter(is_active=True)
    elif status_filter == 'nonaktif':
        qs = qs.filter(is_active=False)

    type_filter = request.GET.get('type', '')
    if type_filter in ('pos', 'mako'):
        qs = qs.filter(type=type_filter)

    return render(request, 'locations/daftar_lokasi.html', {
        'locations': qs,
        'search': search,
        'status_filter': status_filter,
        'type_filter': type_filter,
    })


@login_required
def location_create(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lokasi berhasil ditambahkan.')
            return redirect('locations:daftar')
    else:
        form = LocationForm()

    return render(request, 'locations/form_lokasi.html', {
        'form': form,
        'location': None,
    })


@login_required
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)
    sprin_linked = _check_sprin_linked(location)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lokasi berhasil diperbarui.')
            return redirect('locations:daftar')
    else:
        form = LocationForm(instance=location)

    return render(request, 'locations/form_lokasi.html', {
        'form': form,
        'location': location,
        'sprin_linked': sprin_linked,
    })


@login_required
def location_map(request):
    locations = Location.objects.filter(is_active=True)
    locations_data = [
        {
            'id': loc.pk,
            'name': loc.name,
            'type': loc.get_type_display(),
            'lat': float(loc.latitude),
            'lng': float(loc.longitude),
            'radius': loc.radius,
        }
        for loc in locations
    ]
    return render(request, 'locations/peta_lokasi.html', {
        'locations_data': locations_data,
        'total': locations.count(),
    })
