from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from finance.models import Transaction, Category
from finance.forms import TransactionForm, CategoryForm
import matplotlib.pyplot as plt
import io
import urllib, base64
from django.db.models.functions import TruncMonth


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
@login_required
def analysis(request):
    # Ustawienie backendu matplotlib na 'Agg' (nieinteraktywny), aby uniknąć błędów serwera
    plt.switch_backend('AGG')

    transactions = Transaction.objects.filter(user=request.user)

    # --- WYKRES 1: Kołowy (Wydatki według kategorii) ---
    expenses = transactions.filter(category__type='EXPENSE').values('category__name').annotate(sum=Sum('amount'))
    
    pie_chart = None
    if expenses:
        labels = [item['category__name'] for item in expenses]
        sizes = [item['sum'] for item in expenses]
        
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Zapewnia, że wykres jest kołem
        ax.set_title('Procentowy udział wydatków')

        # Zapisywanie wykresu do bufora
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)
        pie_chart = uri
        plt.close(fig) # Zamknij figurę, by zwolnić pamięć

    # --- WYKRES 2: Słupkowy (Miesiąc po miesiącu: Przychody vs Wydatki) ---
    # Grupujemy transakcje po miesiącach
    monthly_data = transactions.annotate(month=TruncMonth('date')).values('month', 'category__type').annotate(total=Sum('amount')).order_by('month')

    bar_chart = None
    if monthly_data:
        # Przetwarzanie danych do formatu łatwego dla matplotlib
        data_dict = {}
        for item in monthly_data:
            month_str = item['month'].strftime("%Y-%m")
            if month_str not in data_dict:
                data_dict[month_str] = {'INCOME': 0, 'EXPENSE': 0}
            data_dict[month_str][item['category__type']] = float(item['total']) # Konwersja Decimal na float dla wykresu

        months = list(data_dict.keys())
        incomes = [data_dict[m]['INCOME'] for m in months]
        expenses = [data_dict[m]['EXPENSE'] for m in months]

        x = range(len(months))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        rects1 = ax.bar([i - width/2 for i in x], incomes, width, label='Przychody', color='green')
        rects2 = ax.bar([i + width/2 for i in x], expenses, width, label='Wydatki', color='red')

        ax.set_ylabel('Kwota (PLN)')
        ax.set_title('Bilans miesięczny')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)
        ax.legend()

        fig.tight_layout()

        # Zapisywanie wykresu do bufora
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)
        bar_chart = uri
        plt.close(fig)

    return render(request, 'finance/analysis.html', {
        'pie_chart': pie_chart,
        'bar_chart': bar_chart
    })