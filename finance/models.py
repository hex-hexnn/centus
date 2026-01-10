from django.db import models
from django.contrib.auth.models import User  # Do przypisywania danych do użytkownika


class Category(models.Model):
    TYPE_CHOICES = (
        ('INCOME', 'Dochód'),
        ('EXPENSE', 'Wydatek'),
    )
    name = models.CharField(max_length=100, verbose_name="Nazwa kategorii")
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default='EXPENSE')

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Każdy widzi tylko swoje finanse
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota")
    description = models.TextField(blank=True, verbose_name="Opis")
    date = models.DateField(verbose_name="Data transakcji")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']  # Najnowsze na górze
        verbose_name = "Transakcja"
        verbose_name_plural = "Transakcje"

    def __str__(self):
        return f"{self.amount} PLN - {self.category.name}"


class BudgetLimit(models.Model):
    """Limit wydatków na daną kategorię w danym miesiącu"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField(help_text="Wybierz pierwszy dzień miesiąca, którego dotyczy limit")

    class Meta:
        unique_together = ('user', 'category', 'month')  # Unikalny limit dla usera/kategorii/miesiąca

    def __str__(self):
        return f"Limit {self.category.name}: {self.limit_amount}"

    class Subscription(models.Model):
        # Wybór jak często płacimy
        FREQUENCY_CHOICES = [
            ('MONTHLY', 'Co miesiąc'),
            ('YEARLY', 'Co rok'),
        ]

        user = models.ForeignKey(User, on_delete=models.CASCADE)
        category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
        name = models.CharField(max_length=100, verbose_name="Nazwa subskrypcji")
        amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota")

        # Następna płatność
        next_payment_date = models.DateField(verbose_name="Data następnej płatności")
        frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='MONTHLY',
                                     verbose_name="Częstotliwość")
        is_active = models.BooleanField(default=True, verbose_name="Aktywna")

        def __str__(self):
            return f"{self.name} ({self.amount} zł)"