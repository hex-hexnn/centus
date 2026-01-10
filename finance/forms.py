from django import forms
from finance.models import Transaction, Category# <--- Dodałem kropkę przed models
from finance.models import Subscription

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

# Upewnij się, że ta linia jest "przyklejona" do lewej krawędzi (bez spacji przed 'class')
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type']
        labels = {
            'name': 'Nazwa kategorii',
            'type': 'Rodzaj (Wpływ/Wydatek)'
        }

        class SubscriptionForm(forms.ModelForm):
            class Meta:
                model = Subscription
                fields = ['name', 'category', 'amount', 'next_payment_date', 'frequency']
                widgets = {
                    'next_payment_date': forms.DateInput(attrs={'type': 'date'}),
                }