from django import forms

from accounts.models import Personel
from .models import ShiftSchedule


class ScheduleForm(forms.ModelForm):
    personnel = forms.ModelMultipleChoiceField(
        queryset=Personel.objects.none(),
        required=False,
    )

    class Meta:
        model = ShiftSchedule
        fields = ['date', 'shift_type', 'location']
