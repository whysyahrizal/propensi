import json
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from cuti.models import PengajuanCuti
from locations.models import Location

from .models import ShiftSchedule, ShiftSchedulePersonnel


class ScheduleAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Referensi: pimpinan + superadmin. SIRAGA: superadmin + cek MenuItem."""

    allowed_roles = ('pimpinan', 'superadmin')

    def test_func(self):
        user = self.request.user
        if getattr(user, 'role', None) not in self.allowed_roles:
            return False
        if user.is_superadmin:
            return True
        if user.role_obj:
            return user.role_obj.menus.filter(path='schedules:calendar', is_active=True).exists()
        return True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied('Anda tidak memiliki akses ke manajemen jadwal.')
        return super().handle_no_permission()


class CalendarView(ScheduleAccessMixin, TemplateView):
    template_name = 'schedules/calendar.html'


class ScheduleListView(ScheduleAccessMixin, TemplateView):
    template_name = 'schedules/schedule_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schedule_list'] = _base_schedule_queryset_for_user(self.request.user).order_by(
            'date', 'shift_type', 'location__name'
        )
        return context


class PersonnelScheduleAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Personel hanya melihat jadwal sendiri (halaman my_schedule)."""

    def test_func(self):
        return getattr(self.request.user, 'role', None) == 'personel'

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied('Halaman ini hanya untuk personel.')
        return super().handle_no_permission()


class MyScheduleListView(PersonnelScheduleAccessMixin, TemplateView):
    template_name = 'schedules/my_schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        shift_sort_order = Case(
            When(schedule__shift_type=ShiftSchedule.SHIFT_PAGI, then=Value(1)),
            When(schedule__shift_type=ShiftSchedule.SHIFT_SIANG, then=Value(2)),
            When(schedule__shift_type=ShiftSchedule.SHIFT_MALAM, then=Value(3)),
            default=Value(99),
            output_field=IntegerField(),
        )
        assignments = (
            ShiftSchedulePersonnel.objects
            .filter(personel=self.request.user, schedule__date__gte=today)
            .select_related('schedule', 'schedule__location')
            .annotate(_shift_order=shift_sort_order)
            .order_by('schedule__date', '_shift_order', 'schedule__location__name')
        )

        timeline = [assignment.schedule for assignment in assignments]
        today_shift = next(
            (assignment.schedule for assignment in assignments if assignment.schedule.date == today),
            None,
        )

        context['today_shift'] = today_shift
        context['timeline_schedules'] = timeline
        context['today'] = today
        return context


def _base_schedule_queryset_for_user(user):
    qs = ShiftSchedule.objects.select_related('location').prefetch_related('personnel_assignments__personel')
    if user.role == 'pimpinan':
        if not user.satker_id:
            return qs.none()
        qs = qs.filter(personnel_assignments__personel__satker_id=user.satker_id).distinct()
    return qs


def _get_schedule_for_user(user, schedule_id):
    return _base_schedule_queryset_for_user(user).filter(pk=schedule_id).first()


def _schedule_to_event(schedule, user):
    assignments = schedule.personnel_assignments.select_related('personel')
    if user.role == 'pimpinan' and user.satker_id:
        assignments = assignments.filter(personel__satker_id=user.satker_id)

    personnel_objects = [
        {
            'id': assignment.personel_id,
            'name': assignment.personel.nama_lengkap,
            'nrp': assignment.personel.nrp,
        }
        for assignment in assignments
    ]
    personnel_names = [obj['name'] for obj in personnel_objects]
    start_dt, end_dt = schedule.get_start_end()
    can_edit = schedule.date >= timezone.localdate()
    return {
        'id': schedule.pk,
        'title': schedule.get_shift_type_display(),
        'start': start_dt.isoformat(),
        'end': end_dt.isoformat(),
        'editable': can_edit,
        'extendedProps': {
            'shiftName': schedule.get_shift_type_display(),
            'shiftKey': schedule.shift_type,
            'locationName': schedule.location.name,
            'locationId': schedule.location_id,
            'personnel': personnel_names,
            'personnelObjects': personnel_objects,
            'personnelCount': len(personnel_names),
            'isEditable': can_edit,
        },
    }


def _get_assignable_personnel_queryset(user):
    qs = user.__class__.objects.filter(is_active=True, role='personel')
    if user.role == 'pimpinan':
        if not user.satker_id:
            return qs.none()
        qs = qs.filter(satker_id=user.satker_id)
    return qs.order_by('nama_lengkap')


def _validate_personnel_scope(user, personnel_ids):
    if user.role != 'pimpinan':
        return
    valid_ids = set(_get_assignable_personnel_queryset(user).values_list('id', flat=True))
    invalid_ids = [pid for pid in personnel_ids if pid not in valid_ids]
    if invalid_ids:
        raise PermissionDenied('Personel di luar satker Anda tidak dapat dijadwalkan.')


def _build_conflict_map(date_value, shift_type=None, exclude_schedule_id=None):
    conflict_map = {}
    cuti_ids = (
        PengajuanCuti.objects.filter(
            status='disetujui',
            tanggal_mulai__lte=date_value,
            tanggal_selesai__gte=date_value,
        )
        .values_list('personel_id', flat=True)
        .distinct()
    )
    for pid in cuti_ids:
        conflict_map[pid] = 'Sedang Cuti'

    shift_labels = dict(ShiftSchedule.SHIFT_CHOICES)
    assignment_qs = ShiftSchedulePersonnel.objects.filter(schedule__date=date_value)
    if shift_type:
        assignment_qs = assignment_qs.filter(schedule__shift_type=shift_type)
    if exclude_schedule_id:
        assignment_qs = assignment_qs.exclude(schedule_id=exclude_schedule_id)
    for row in assignment_qs.values('personel_id', 'schedule__shift_type'):
        pid = row['personel_id']
        if pid not in conflict_map:
            st = row['schedule__shift_type']
            conflict_map[pid] = f"Sudah dijadwalkan di shift {shift_labels.get(st, st)}"
    return conflict_map


def _validate_personnel_shift_conflict(date_value, shift_type, personnel_ids, exclude_schedule_id=None):
    if not personnel_ids:
        return

    existing = (
        ShiftSchedulePersonnel.objects
        .filter(
            schedule__date=date_value,
            schedule__shift_type=shift_type,
            personel_id__in=personnel_ids,
        )
        .select_related('personel')
    )
    if exclude_schedule_id:
        existing = existing.exclude(schedule_id=exclude_schedule_id)

    conflicted = list(existing)
    if conflicted:
        names = ', '.join(sorted({item.personel.nama_lengkap for item in conflicted}))
        shift_display = dict(ShiftSchedule.SHIFT_CHOICES).get(shift_type, shift_type)
        raise PermissionDenied(
            f'Personel sudah terjadwal pada waktu yang sama (Shift {shift_display}). Bentrok: {names}.'
        )


def _parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return None


def _assigner_display_name(user):
    pangkat = (getattr(user, 'pangkat', None) or '').strip()
    nama = (getattr(user, 'nama_lengkap', None) or '').strip()
    parts = [p for p in (pangkat, nama) if p]
    if parts:
        return ' '.join(parts)
    return getattr(user, 'nrp', None) or f'User #{user.pk}'


def _enqueue_shift_assignment_notifications(personnel_ids, assigner, schedule, extra_lead=None):
    """Notifikasi ke personel (accounts.Personel) setelah jadwal di-assign / diubah."""
    if not personnel_ids:
        return
    ids = list(dict.fromkeys(int(x) for x in personnel_ids))
    assigner_name = _assigner_display_name(assigner)
    date_str = schedule.date.strftime('%d %b %Y')

    def send():
        from django.urls import reverse

        from notifikasi.utils import kirim_notifikasi

        link = reverse('schedules:my_schedule')
        judul = 'Penugasan jadwal piket'
        body = (
            f"Shift {schedule.get_shift_type_display()}, {date_str}, lokasi {schedule.location.name}.\n\n"
            f"Ditugaskan oleh: {assigner_name}"
        )
        if extra_lead:
            body = f"{extra_lead}\n\n{body}"
        User = assigner.__class__
        for personel in User.objects.filter(pk__in=ids, is_active=True, role='personel'):
            kirim_notifikasi(
                user=personel,
                judul=judul,
                pesan=body,
                tipe='jadwal',
                link=link,
                kirim_email=False,
            )

    transaction.on_commit(send)


def _enqueue_shift_deletion_notifications(personnel_ids, assigner, *, tanggal, shift_label, lokasi_nama):
    """Notifikasi ke personel saat jadwal shift mereka dihapus."""
    if not personnel_ids:
        return
    ids = list(dict.fromkeys(int(x) for x in personnel_ids))
    assigner_name = _assigner_display_name(assigner)

    def send():
        from django.urls import reverse

        from notifikasi.utils import kirim_notifikasi

        link = reverse('schedules:my_schedule')
        judul = 'Jadwal piket dihapus'
        body = (
            f"Jadwal shift {shift_label} pada {tanggal}, lokasi {lokasi_nama}, telah dihapus dari sistem.\n\n"
            f"Dihapus oleh: {assigner_name}"
        )
        User = assigner.__class__
        for personel in User.objects.filter(pk__in=ids, is_active=True, role='personel'):
            kirim_notifikasi(
                user=personel,
                judul=judul,
                pesan=body,
                tipe='jadwal',
                link=link,
                kirim_email=False,
            )

    transaction.on_commit(send)


def _enqueue_shift_removed_from_assignment_notifications(personnel_ids, assigner, schedule):
    """Personel dikeluarkan dari daftar penugasan (update jadwal), bukan hapus seluruh jadwal."""
    if not personnel_ids:
        return
    ids = list(dict.fromkeys(int(x) for x in personnel_ids))
    assigner_name = _assigner_display_name(assigner)
    date_str = schedule.date.strftime('%d %b %Y')
    shift_label = schedule.get_shift_type_display()
    lokasi_nama = schedule.location.name

    def send():
        from django.urls import reverse

        from notifikasi.utils import kirim_notifikasi

        link = reverse('schedules:my_schedule')
        judul = 'Penugasan jadwal diperbarui'
        body = (
            f"Anda tidak lagi ditugaskan pada shift {shift_label}, {date_str}, lokasi {lokasi_nama}.\n\n"
            f"Diubah oleh: {assigner_name}"
        )
        User = assigner.__class__
        for personel in User.objects.filter(pk__in=ids, is_active=True, role='personel'):
            kirim_notifikasi(
                user=personel,
                judul=judul,
                pesan=body,
                tipe='jadwal',
                link=link,
                kirim_email=False,
            )

    transaction.on_commit(send)


class ScheduleEventsApiView(ScheduleAccessMixin, View):
    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        qs = _base_schedule_queryset_for_user(request.user)
        if start:
            qs = qs.filter(date__gte=start[:10])
        if end:
            qs = qs.filter(date__lte=end[:10])

        shift_sort_order = Case(
            When(shift_type=ShiftSchedule.SHIFT_PAGI, then=Value(1)),
            When(shift_type=ShiftSchedule.SHIFT_SIANG, then=Value(2)),
            When(shift_type=ShiftSchedule.SHIFT_MALAM, then=Value(3)),
            default=Value(99),
            output_field=IntegerField(),
        )
        qs = qs.annotate(_shift_order=shift_sort_order).order_by('date', '_shift_order', 'location__name')
        events = [_schedule_to_event(schedule, request.user) for schedule in qs]
        return JsonResponse(events, safe=False)


class LocationOptionsApiView(ScheduleAccessMixin, View):
    def get(self, request):
        keyword = request.GET.get('q', '').strip()
        type_labels = dict(Location.TYPE_CHOICES)
        qs = Location.objects.filter(is_active=True).order_by('name')
        if keyword:
            qs = qs.filter(name__icontains=keyword)
        data = [
            {
                'id': row['id'],
                'name': row['name'],
                'type': type_labels.get(row['type'], row['type']),
                'radius': row['radius'],
            }
            for row in qs.values('id', 'name', 'type', 'radius')
        ]
        return JsonResponse({'results': data})


class PersonnelOptionsApiView(ScheduleAccessMixin, View):
    def get(self, request):
        date_str = request.GET.get('date')
        shift_type = request.GET.get('shift_type')
        if not date_str:
            return JsonResponse({'error': 'Parameter date wajib diisi.'}, status=400)
        try:
            date_value = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Format date tidak valid.'}, status=400)

        if shift_type and shift_type not in {choice[0] for choice in ShiftSchedule.SHIFT_CHOICES}:
            return JsonResponse({'error': 'shift_type tidak valid.'}, status=400)

        exclude_schedule_id = request.GET.get('exclude_schedule_id')
        conflict_map = _build_conflict_map(date_value, shift_type, exclude_schedule_id)
        personel_qs = _get_assignable_personnel_queryset(request.user)
        search_q = request.GET.get('q', '').strip()
        if search_q:
            personel_qs = personel_qs.filter(
                Q(nama_lengkap__icontains=search_q) | Q(nrp__icontains=search_q)
            )
        results = [
            {
                'id': row['id'],
                'name': row['nama_lengkap'],
                'nrp': row['nrp'],
                'conflict': conflict_map.get(row['id']),
            }
            for row in personel_qs.values('id', 'nama_lengkap', 'nrp')
        ]
        return JsonResponse({'results': results})


class ScheduleCreateView(ScheduleAccessMixin, View):
    def post(self, request):
        payload = _parse_json(request)
        if payload is None:
            return JsonResponse({'error': 'Payload JSON tidak valid.'}, status=400)

        date_str = payload.get('date')
        shift_type = payload.get('shift_type')
        location_id = payload.get('location_id')
        personnel_ids = payload.get('personnel_ids', [])

        date_str = (str(date_str).strip() if date_str is not None else '')
        shift_type = (str(shift_type).strip() if shift_type is not None else '')
        if location_id is not None and location_id != '':
            location_id = str(location_id).strip()

        if not date_str or not shift_type or location_id in (None, '', '0', 0):
            return JsonResponse({'error': 'date, shift_type, dan location_id wajib diisi.'}, status=400)

        if shift_type not in {choice[0] for choice in ShiftSchedule.SHIFT_CHOICES}:
            return JsonResponse({'error': 'shift_type tidak valid.'}, status=400)

        try:
            date_value = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Format date tidak valid.'}, status=400)

        if date_value < timezone.localdate():
            return JsonResponse({'error': 'Tidak dapat membuat jadwal untuk tanggal yang sudah lewat.'}, status=400)

        try:
            location_id = int(location_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'location_id tidak valid.'}, status=400)

        if not isinstance(personnel_ids, list):
            return JsonResponse({'error': 'personnel_ids harus berupa list.'}, status=400)
        try:
            personnel_ids = [int(pid) for pid in personnel_ids]
        except (TypeError, ValueError):
            return JsonResponse({'error': 'personnel_ids tidak valid.'}, status=400)

        location = Location.objects.filter(pk=location_id, is_active=True).first()
        if not location:
            return JsonResponse({'error': 'Lokasi tidak valid atau nonaktif.'}, status=400)

        try:
            _validate_personnel_scope(request.user, personnel_ids)
            _validate_personnel_shift_conflict(date_value, shift_type, personnel_ids)
        except PermissionDenied as e:
            return JsonResponse({'error': str(e)}, status=403)

        schedule, created = ShiftSchedule.objects.get_or_create(
            date=date_value,
            shift_type=shift_type,
            location=location,
            defaults={'created_by': request.user},
        )
        if not created:
            try:
                _validate_personnel_scope(request.user, personnel_ids)
                _validate_personnel_shift_conflict(
                    date_value,
                    shift_type,
                    personnel_ids,
                    exclude_schedule_id=schedule.id,
                )
            except PermissionDenied as e:
                return JsonResponse({'error': str(e)}, status=403)

            existing_ids = set(schedule.personnel_assignments.values_list('personel_id', flat=True))
            ids_to_add = [pid for pid in personnel_ids if pid not in existing_ids]
            if ids_to_add:
                selected_personel = _get_assignable_personnel_queryset(request.user).filter(id__in=ids_to_add)
                assignments = [
                    ShiftSchedulePersonnel(schedule=schedule, personel=personel)
                    for personel in selected_personel
                ]
                ShiftSchedulePersonnel.objects.bulk_create(assignments, ignore_conflicts=True)

            schedule = ShiftSchedule.objects.select_related('location').prefetch_related(
                'personnel_assignments__personel'
            ).get(pk=schedule.pk)
            if ids_to_add:
                _enqueue_shift_assignment_notifications(ids_to_add, request.user, schedule)
            msg = (
                'Personel ditambahkan pada jadwal yang sudah ada untuk slot ini.'
                if ids_to_add
                else 'Jadwal untuk slot ini sudah ada; tidak ada personel baru untuk ditambahkan.'
            )
            return JsonResponse({'message': msg, 'event': _schedule_to_event(schedule, request.user)})

        selected_personel = _get_assignable_personnel_queryset(request.user).filter(id__in=personnel_ids)
        assignments = [ShiftSchedulePersonnel(schedule=schedule, personel=personel) for personel in selected_personel]
        ShiftSchedulePersonnel.objects.bulk_create(assignments, ignore_conflicts=True)

        schedule = ShiftSchedule.objects.select_related('location').prefetch_related('personnel_assignments__personel').get(
            pk=schedule.pk
        )
        if personnel_ids:
            _enqueue_shift_assignment_notifications(personnel_ids, request.user, schedule)
        return JsonResponse({'message': 'Jadwal berhasil dibuat.', 'event': _schedule_to_event(schedule, request.user)})


class ScheduleUpdateView(ScheduleAccessMixin, View):
    def post(self, request, schedule_id):
        schedule = _get_schedule_for_user(request.user, schedule_id)
        if not schedule:
            return JsonResponse({'error': 'Jadwal tidak ditemukan.'}, status=404)

        if schedule.date < timezone.localdate():
            return JsonResponse({'error': 'Data historis tidak dapat diubah.'}, status=403)

        payload = _parse_json(request)
        if payload is None:
            return JsonResponse({'error': 'Payload JSON tidak valid.'}, status=400)

        shift_type = payload.get('shift_type', schedule.shift_type)
        location_id = payload.get('location_id', schedule.location_id)
        personnel_ids = payload.get('personnel_ids', None)

        if shift_type not in {choice[0] for choice in ShiftSchedule.SHIFT_CHOICES}:
            return JsonResponse({'error': 'shift_type tidak valid.'}, status=400)

        try:
            location_id = int(location_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'location_id tidak valid.'}, status=400)

        location = Location.objects.filter(pk=location_id, is_active=True).first()
        if not location:
            return JsonResponse({'error': 'Lokasi tidak valid atau nonaktif.'}, status=400)

        exists = ShiftSchedule.objects.filter(
            date=schedule.date,
            shift_type=shift_type,
            location_id=location_id,
        ).exclude(pk=schedule.pk).exists()
        if exists:
            return JsonResponse({'error': 'Jadwal tersebut sudah ada'}, status=400)

        schedule.shift_type = shift_type
        schedule.location = location
        schedule.save(update_fields=['shift_type', 'location', 'updated_at'])

        if personnel_ids is not None:
            if not isinstance(personnel_ids, list):
                return JsonResponse({'error': 'personnel_ids harus berupa list.'}, status=400)
            try:
                personnel_ids = [int(pid) for pid in personnel_ids]
            except (TypeError, ValueError):
                return JsonResponse({'error': 'personnel_ids tidak valid.'}, status=400)
            try:
                _validate_personnel_scope(request.user, personnel_ids)
                _validate_personnel_shift_conflict(
                    schedule.date,
                    shift_type,
                    personnel_ids,
                    exclude_schedule_id=schedule.id,
                )
            except PermissionDenied as e:
                return JsonResponse({'error': str(e)}, status=403)
            old_personnel_ids = set(schedule.personnel_assignments.values_list('personel_id', flat=True))
            new_ids = set(personnel_ids)
            removed_ids = list(old_personnel_ids - new_ids)
            schedule.personnel_assignments.all().delete()
            selected_personel = _get_assignable_personnel_queryset(request.user).filter(id__in=personnel_ids)
            assignments = [ShiftSchedulePersonnel(schedule=schedule, personel=personel) for personel in selected_personel]
            ShiftSchedulePersonnel.objects.bulk_create(assignments, ignore_conflicts=True)
            added_ids = list(new_ids - old_personnel_ids)
            if removed_ids:
                _enqueue_shift_removed_from_assignment_notifications(removed_ids, request.user, schedule)
            if added_ids:
                _enqueue_shift_assignment_notifications(added_ids, request.user, schedule)

        schedule = ShiftSchedule.objects.select_related('location').prefetch_related('personnel_assignments__personel').get(
            pk=schedule.pk
        )
        return JsonResponse({'message': 'Jadwal berhasil diperbarui.', 'event': _schedule_to_event(schedule, request.user)})


class ScheduleDeleteView(ScheduleAccessMixin, View):
    def post(self, request, schedule_id):
        schedule = _get_schedule_for_user(request.user, schedule_id)
        if not schedule:
            return JsonResponse({'error': 'Jadwal tidak ditemukan.'}, status=404)

        if schedule.date < timezone.localdate():
            return JsonResponse({'error': 'Data historis tidak dapat diubah.'}, status=403)

        personnel_ids = list(schedule.personnel_assignments.values_list('personel_id', flat=True))
        tanggal = schedule.date.strftime('%d %b %Y')
        shift_label = schedule.get_shift_type_display()
        lokasi_nama = schedule.location.name
        schedule.delete()
        if personnel_ids:
            _enqueue_shift_deletion_notifications(
                personnel_ids,
                request.user,
                tanggal=tanggal,
                shift_label=shift_label,
                lokasi_nama=lokasi_nama,
            )
        return JsonResponse({'message': 'Jadwal berhasil dihapus.'})


class ScheduleMoveView(ScheduleAccessMixin, View):
    def post(self, request, schedule_id):
        schedule = _get_schedule_for_user(request.user, schedule_id)
        if not schedule:
            return JsonResponse({'error': 'Jadwal tidak ditemukan.'}, status=404)

        if schedule.date < timezone.localdate():
            return JsonResponse({'error': 'Data historis tidak dapat diubah.'}, status=403)

        payload = _parse_json(request)
        if payload is None:
            return JsonResponse({'error': 'Payload JSON tidak valid.'}, status=400)

        new_date_str = payload.get('new_date')
        if not new_date_str:
            return JsonResponse({'error': 'new_date wajib diisi.'}, status=400)
        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Format new_date tidak valid.'}, status=400)

        if new_date < timezone.localdate():
            return JsonResponse({'error': 'Tidak dapat memindahkan jadwal ke tanggal yang sudah lewat.'}, status=400)

        exists = ShiftSchedule.objects.filter(
            date=new_date,
            shift_type=schedule.shift_type,
            location_id=schedule.location_id,
        ).exclude(pk=schedule.pk).exists()
        if exists:
            return JsonResponse({'error': 'Jadwal bentrok: sudah ada pada tanggal baru.'}, status=400)

        assigned_personnel_ids = list(schedule.personnel_assignments.values_list('personel_id', flat=True))
        try:
            _validate_personnel_shift_conflict(
                new_date,
                schedule.shift_type,
                assigned_personnel_ids,
                exclude_schedule_id=schedule.id,
            )
        except PermissionDenied as e:
            return JsonResponse({'error': str(e)}, status=403)

        schedule.date = new_date
        schedule.save(update_fields=['date', 'updated_at'])
        if assigned_personnel_ids:
            _enqueue_shift_assignment_notifications(
                assigned_personnel_ids,
                request.user,
                schedule,
                extra_lead=f'Jadwal dipindahkan ke tanggal {new_date.strftime("%d %b %Y")}.',
            )
        schedule = ShiftSchedule.objects.select_related('location').prefetch_related('personnel_assignments__personel').get(
            pk=schedule.pk
        )
        return JsonResponse({'message': 'Jadwal berhasil dipindahkan.', 'event': _schedule_to_event(schedule, request.user)})
