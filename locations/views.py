import json
import urllib.parse
import urllib.request

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from accounts.decorators import cek_akses_menu

from .models import Location
from .forms import LocationForm


def _ensure_location_management_access(request):
    if request.user.role not in ('pimpinan', 'superadmin'):
        raise PermissionDenied('Anda tidak memiliki akses ke manajemen wilayah.')


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
@cek_akses_menu('locations:daftar')
def location_list(request):
    _ensure_location_management_access(request)
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
@cek_akses_menu('locations:daftar')
def location_create(request):
    _ensure_location_management_access(request)
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
@cek_akses_menu('locations:daftar')
def location_edit(request, pk):
    _ensure_location_management_access(request)
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
        'location_data': {
            'lat': float(location.latitude),
            'lng': float(location.longitude),
            'radius': location.radius,
        },
    })


@login_required
@cek_akses_menu('locations:daftar')
def location_map(request):
    _ensure_location_management_access(request)
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


@login_required
@cek_akses_menu('locations:daftar')
@require_GET
def geocode_search(request):
    _ensure_location_management_access(request)
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    params = urllib.parse.urlencode({
        'q': query,
        'format': 'jsonv2',
        'addressdetails': 1,
        'limit': 5,
        'countrycodes': 'id',
    })
    url = f'https://nominatim.openstreetmap.org/search?{params}'
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'SIRAGA-Geocoder/1.0',
            'Accept': 'application/json',
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except Exception:
        return JsonResponse({'results': [], 'error': 'Layanan geocoding sedang tidak tersedia.'}, status=502)

    results = []
    for item in payload:
        try:
            lat = float(item.get('lat'))
            lon = float(item.get('lon'))
        except (TypeError, ValueError):
            continue
        results.append({
            'display_name': item.get('display_name') or 'Alamat tidak diketahui',
            'lat': lat,
            'lon': lon,
        })
    return JsonResponse({'results': results})
