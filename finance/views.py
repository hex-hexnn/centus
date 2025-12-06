from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Transaction
from .forms import TransactionForm


@login_required  # Wymaga zalogowania - o tym niżej w sekcji uruchamiania
def transaction_list(request):
    # Pobieramy transakcje TYLKO zalogowanego użytkownika
    transactions = Transaction.objects.filter(user=request.user)

    # Mała analiza na szybko - suma wpływów i wydatków
    total_income = transactions.filter(category__type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(category__type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense

    return render(request, 'finance/transaction_list.html', {
        'transactions': transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance
    })


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            # commit=False tworzy obiekt w pamięci, ale jeszcze nie w bazie
            transaction = form.save(commit=False)
            # Przypisujemy transakcję do aktualnie zalogowanego użytkownika
            transaction.user = request.user
            transaction.save()  # Teraz zapisujemy do bazy
            return redirect('transaction_list')
    else:
        form = TransactionForm()

    return render(request, 'finance/transaction_form.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Opcjonalne: Zaloguj użytkownika od razu po rejestracji
            login(request, user)
            return redirect('transaction_list')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})