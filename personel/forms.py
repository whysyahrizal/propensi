from django import forms
from .models import Personel

class PersonelForm(forms.ModelForm):
    class Meta:
        model = Personel
        fields = ['nama', 'nip', 'unit']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan nama'}),
            'nip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan NIP'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_nip(self):
        nip = self.cleaned_data['nip'].strip()
        qs = Personel.objects.filter(nip=nip)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('NIP sudah digunakan.')
        if not nip.isdigit():
            raise forms.ValidationError('NIP harus berupa angka.')
        if len(nip) != 8:
            raise forms.ValidationError('NIP harus tepat 8 digit.')
        return nip