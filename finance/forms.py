from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        # Wybieramy pola, które użytkownik może edytować
        fields = ['category', 'amount', 'date', 'description']
        # Dodajemy widget, żeby data była kalendarzem, a nie zwykłym tekstem
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }