from django import forms
from .models import Order, Review

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


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'phone', 'size', 'note']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ismingiz'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67', 'type': 'tel'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': "Qo'shimcha izoh (ixtiyoriy)"}),
        }
        labels = {
            'customer_name': 'Ismingiz',
            'phone': 'Telefon raqamingiz',
            'size': "O'lcham",
            'note': 'Izoh',
        }

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        sizes = product.size_list if product else []
        if sizes:
            self.fields['size'].widget.choices = [('', 'Tanlang / bilmayman')] + [(s, s) for s in sizes]
        else:
            del self.fields['size']

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if sum(c.isdigit() for c in phone) < 7:
            raise forms.ValidationError("Telefon raqamni to'g'ri kiriting.")
        return phone
