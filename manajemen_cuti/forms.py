from django import forms
from .models import PengajuanCuti
from accounts.models import Satker

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = PengajuanCuti
        fields = ['jenis_cuti', 'satuan_kerja', 'tanggal_mulai', 'tanggal_selesai', 'alasan', 'lampiran']
        widgets = {
            'tanggal_mulai': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}, format='%Y-%m-%d'),
            'tanggal_selesai': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}, format='%Y-%m-%d'),
            'alasan': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'Jelaskan alasan pengajuan...'}),
            'jenis_cuti': forms.Select(attrs={'class': 'form-input'}),
            'satuan_kerja': forms.Select(attrs={'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tanggal_mulai = cleaned_data.get('tanggal_mulai')
        tanggal_selesai = cleaned_data.get('tanggal_selesai')

        if tanggal_mulai and tanggal_selesai:
            if tanggal_mulai > tanggal_selesai:
                raise forms.ValidationError("Tanggal mulai tidak boleh melebihi tanggal selesai.")
        return cleaned_data
