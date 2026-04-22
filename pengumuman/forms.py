from django import forms
from .models import Pengumuman

class PengumumanForm(forms.ModelForm):
    class Meta:
        model = Pengumuman
        fields = ['judul', 'isi', 'periode_mulai', 'periode_selesai', 'is_active']
        error_messages = {
            'judul': {'required': 'Field ini tidak boleh kosong.'},
            'isi': {'required': 'Field ini tidak boleh kosong.'},
        }
        widgets = {
            'judul': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]/30 focus:border-[#1a3a6b] transition', 
                'placeholder': 'Masukkan judul pengumuman'
            }),
            'isi': forms.Textarea(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]/30 focus:border-[#1a3a6b] transition', 
                'rows': 5, 
                'placeholder': 'Masukkan isi pengumuman'
            }),
            'periode_mulai': forms.DateInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]/30 focus:border-[#1a3a6b] transition', 
                'type': 'date'
            }),
            'periode_selesai': forms.DateInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a3a6b]/30 focus:border-[#1a3a6b] transition', 
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded text-[#1a3a6b] focus:ring-[#1a3a6b] w-4 h-4 cursor-pointer'
            })
        }
