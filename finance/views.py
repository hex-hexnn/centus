from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from finance.models import Transaction, Category
from finance.forms import TransactionForm, CategoryForm


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


@login_required
def category_list(request):
    # Pobieramy wszystkie kategorie
    categories = Category.objects.all()
    return render(request, 'finance/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')  # Po sukcesie wracamy do listy kategorii
    else:
        form = CategoryForm()

    return render(request, 'finance/category_form.html', {'form': form})


@login_required
def category_update(request, pk):
    # Pobieramy konkretną kategorię po ID (pk) lub zwracamy błąd 404
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        # Tu jest MAGIA: instance=category mówi formularzowi:
        # "Weź dane z request.POST, ale nadpisz nimi ten konkretny obiekt z bazy"
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        # Wypełniamy formularz aktualnymi danymi z bazy
        form = CategoryForm(instance=category)

    # Używamy tego samego szablonu co przy tworzeniu!
    return render(request, 'finance/category_form.html', {'form': form})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        # Jeśli użytkownik potwierdził usunięcie przyciskiem (metoda POST)
        category.delete()
        return redirect('category_list')

    # Jeśli wszedł tylko na stronę (GET), pytamy czy na pewno
    return render(request, 'finance/category_confirm_delete.html', {'category': category})


@login_required
def transaction_update(request, pk):
    # KROK 1: Pobieramy transakcję, ale TYLKO jeśli należy do użytkownika.
    # Jeśli użytkownik spróbuje edytować cudzą transakcję -> dostanie błąd 404.
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        # KROK 2: Wypełniamy formularz danymi z POST, nadpisując obiekt z bazy (instance)
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('transaction_list')  # Powrót do pulpitu
    else:
        # KROK 3: Jeśli to GET (wejście na stronę), wyświetlamy formularz wypełniony danymi
        form = TransactionForm(instance=transaction)

    # Reużywamy szablonu transaction_form.html! Nie musisz tworzyć nowego.
    return render(request, 'finance/transaction_form.html', {'form': form})


@login_required
def transaction_delete(request, pk):
    # KROK 1: Znów zabezpieczenie - pobieramy tylko własną transakcję
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        # KROK 2: Fizyczne usunięcie z bazy
        transaction.delete()
        return redirect('transaction_list')

    # KROK 3: Wyświetlenie strony z pytaniem "Czy na pewno?"
    return render(request, 'finance/transaction_confirm_delete.html', {'transaction': transaction})