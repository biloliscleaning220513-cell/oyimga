from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['client_name', 'purchase_date', 'phone_number', 'video']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ismingiz va familiyangizni kiriting',
                'required': True
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998 90 123 45 67'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
        }
        labels = {
            'client_name': 'Ismingiz (Majburiy)',
            'purchase_date': 'Mahsulotni sotib olgan sanangiz (Majburiy)',
            'phone_number': 'Telefon raqamingiz (Ixtiyoriy - Shart 1)',
            'video': 'Mahsulot videosi (Ixtiyoriy - Shart 2)',
        }
