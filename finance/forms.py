from django import forms
from finance.models import Transaction, Category, Subscription # <--- Dodałem kropkę przed models
from django import forms
from datetime import date
from .models import BudgetLimit, Category


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
        fields = ['name', 'amount', 'payment_day']
        widgets = {
            'payment_day': forms.NumberInput(attrs={'min': 1, 'max': 31}),
        }
        
class BudgetLimitForm(forms.ModelForm):
    # Użytkownik wybiera miesiąc (YYYY-MM), a my zamieniamy na pierwszy dzień miesiąca
    month = forms.DateField(
    input_formats=["%Y-%m", "%Y-%m-%d"],
    widget=forms.DateInput(attrs={"type": "month", "class": "form-control"}),
    help_text="Wybierz miesiąc limitu",
)


    class Meta:
        model = BudgetLimit
        fields = ["category", "limit_amount", "month"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "limit_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limity sensownie ustawiać tylko dla wydatków
        self.fields["category"].queryset = Category.objects.filter(type="EXPENSE")

        # jeśli edytujemy istniejący rekord, to month pokaż jako YYYY-MM
        if self.instance and self.instance.pk and self.instance.month:
            self.initial["month"] = self.instance.month.replace(day=1)

    def clean_month(self):
        m = self.cleaned_data["month"]
        return date(m.year, m.month, 1)