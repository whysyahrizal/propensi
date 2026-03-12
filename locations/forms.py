from django import forms
from .models import Location


class LocationForm(forms.ModelForm):
    is_active = forms.BooleanField(required=False, initial=True, label='Aktif')

    class Meta:
        model = Location
        fields = ['name', 'type', 'latitude', 'longitude', 'radius', 'is_active']
