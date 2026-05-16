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
import calendar
from datetime import date, datetime
from finance.models import Subscription
from finance.forms import SubscriptionForm
from finance.recommendations import get_savings_recommendations
from finance.models import BudgetLimit
from finance.forms import BudgetLimitForm
from django.contrib import messages
from .forms import ReceiptForm
from .models import Receipt
import pytesseract
from PIL import Image

#--- tutaj wpisujecie lokacje gdzie macie pobrany tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


@login_required
def transaction_list(request):
    # Pobieramy transakcje TYLKO zalogowanego użytkownika
    transactions = Transaction.objects.filter(user=request.user)

    # Obliczenia sum
    total_income = transactions.filter(category__type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(category__type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense

    # --- NOWOŚĆ: Generowanie ogólnego wykresu (Pulpit) ---
    dashboard_chart = None
    if total_income > 0 or total_expense > 0:
        plt.switch_backend('AGG') # Ustawiamy backend na nieinteraktywny
        
        # Tworzymy figurę o niestandardowym rozmiarze (szeroka i niska)
        fig, ax = plt.subplots(figsize=(8, 3)) 
        
        categories = ['Przychody', 'Wydatki']
        values = [total_income, total_expense]
        colors = ['#198754', '#dc3545'] # Kolory Bootstrap: Success (zielony) i Danger (czerwony)
        
        # Rysujemy słupki
        bars = ax.bar(categories, values, color=colors, width=0.4)
        
        # Dodajemy wartości nad słupkami dla czytelności
        ax.bar_label(bars, fmt='%.2f zł', padding=3)
        
        ax.set_title('Ogólny Bilans Finansowy')
        
        # Usuwamy ramki wykresu dla czystszego wyglądu (opcjonalne)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        fig.tight_layout()

        # Zapis do bufora
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        dashboard_chart = urllib.parse.quote(string)
        plt.close(fig) # Zamykamy, aby zwolnić pamięć
    # -----------------------------------------------------

    return render(request, 'finance/transaction_list.html', {
        'transactions': transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'dashboard_chart': dashboard_chart, # Przekazujemy wykres do szablonu
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

@login_required
def calendar_view(request):
    # 1. Ustalamy jaki rok i miesiąc wyświetlić (domyślnie obecny)
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # 2. Pobieramy transakcje użytkownika z tego konkretnego miesiąca i roku
    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )

    # 3. Pobieramy wszystkie subskrypcje użytkownika
    subscriptions = Subscription.objects.filter(user=request.user)

    # 4. Tworzymy strukturę danych: Słownik, gdzie kluczem jest DZIEŃ, a wartością lista wydarzeń
    # np. { 10: ['Netflix 50zł', 'Zakupy 120zł'], 15: ['Wypłata'] }
    days_data = {}

    # Dodajemy jednorazowe transakcje do kalendarza
    for trans in transactions:
        day = trans.date.day
        if day not in days_data:
            days_data[day] = []
        days_data[day].append({
            'type': 'trans',
            'name': trans.category.name if trans.category else "Inne",
            'amount': trans.amount,
            'is_income': trans.category.type == 'INCOME' if trans.category else False
        })

    # Dodajemy subskrypcje (powtarzają się co miesiąc)
    for sub in subscriptions:
        # Sprawdzamy, czy dzień płatności istnieje w tym miesiącu (np. luty nie ma 30-go)
        max_days_in_month = calendar.monthrange(year, month)[1]
        if sub.payment_day <= max_days_in_month:
            if sub.payment_day not in days_data:
                days_data[sub.payment_day] = []
            days_data[sub.payment_day].append({
                'type': 'sub',
                'name': sub.name,
                'amount': sub.amount,
                'is_income': False # Zakładamy, że subskrypcja to wydatek
            })

    # 5. Generujemy macierz kalendarza (listę tygodni)
    cal = calendar.monthcalendar(year, month)

    # Obsługa formularza dodawania subskrypcji (prosty sposób na tej samej stronie)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.user = request.user
            sub.save()
            return redirect('calendar') # Przeładuj stronę
    else:
        form = SubscriptionForm()

    context = {
        'calendar_weeks': cal, # Lista list dni np. [[0,0,1,2...], [3,4,5...]]
        'days_data': days_data, # Nasze dane o wydatkach
        'current_year': year,
        'current_month': month,
        'month_name': calendar.month_name[month],
        'form': form, # Formularz do subskrypcji
    }

    return render(request, 'finance/calendar.html', context)

from datetime import date
from finance.recommendations import get_savings_recommendations

@login_required
def recommendations_view(request):
    month_str = request.GET.get("month")
    selected_month = None

    if month_str:
        try:
            selected_month = date.fromisoformat(month_str)
        except ValueError:
            selected_month = None

    recommendations = get_savings_recommendations(request.user, for_month=selected_month)

    context = {
        "recommendations": recommendations,
        "selected_month": selected_month,
    }
    return render(request, "finance/recommendations.html", context)

@login_required
def budget_limits_list(request):
    limits = BudgetLimit.objects.filter(user=request.user).select_related("category").order_by("-month", "category__name")
    return render(request, "finance/budget_limits_list.html", {"limits": limits})


@login_required
def budget_limit_create(request):
    if request.method == "POST":
        form = BudgetLimitForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            try:
                obj.save()
                messages.success(request, "Limit zapisany.")
                return redirect("budget_limits")
            except Exception:
                # najczęściej poleci unique_together (ten sam user+category+miesiąc)
                messages.error(request, "Limit dla tej kategorii i miesiąca już istnieje. Edytuj istniejący.")
    else:
        form = BudgetLimitForm()

    return render(request, "finance/budget_limit_form.html", {"form": form, "title": "Dodaj limit"})


@login_required
def budget_limit_update(request, pk):
    obj = get_object_or_404(BudgetLimit, pk=pk, user=request.user)

    if request.method == "POST":
        form = BudgetLimitForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Limit zaktualizowany.")
            return redirect("budget_limits")
    else:
        form = BudgetLimitForm(instance=obj)

    return render(request, "finance/budget_limit_form.html", {"form": form, "title": "Edytuj limit"})


@login_required
def budget_limit_delete(request, pk):
    obj = get_object_or_404(BudgetLimit, pk=pk, user=request.user)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Limit usunięty.")
        return redirect("budget_limits")
    return render(request, "finance/budget_limit_delete.html", {"obj": obj})


@login_required
def upload_receipt(request):
    if request.method == 'POST':
        form = ReceiptForm(request.POST, request.FILES)

        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.user = request.user
            receipt.save()  # Zapisujemy obiekt, żeby zdjęcie fizycznie trafiło na dysk

            # ---------------------------------------------------------
            # TUTAJ WYKORZYSTUJEMY SKONFIGUROWANEGO TESSERACTA DO OCR:
            # ---------------------------------------------------------
            try:
                # Otwieramy zapisany plik graficzny przy użyciu biblioteki Pillow (Image)
                img = Image.open(receipt.image.path)

                # Przetwarzamy obraz na tekst (używając polskiego pakietu językowego 'pol')
                extracted_text = pytesseract.image_to_string(img, lang='pol')

                # Zapisujemy odczytany tekst do bazy danych w polu 'extracted_text'
                receipt.extracted_text = extracted_text
                receipt.save()

                messages.success(request, "Paragon został pomyślnie przetworzony przez OCR!")
            except Exception as e:
                messages.error(request, f"Błąd podczas odczytywania tekstu ze zdjęcia: {e}")
            # ---------------------------------------------------------

            return redirect('/')  # Przekierowanie na stronę główną pulpitu

    else:
        form = ReceiptForm()

    return render(request, 'finance/upload_receipt.html', {'form': form})


@login_required
def receipt_list(request):
    # 1. Pobieramy paragony użytkownika
    receipts = Receipt.objects.filter(user=request.user).order_by('-uploaded_at')
    # 2. Pobieramy kategorie wydatków do rozwijanej listy formularza
    categories = Category.objects.filter(type='EXPENSE')

    # 3. Obsługa formularza, gdy użytkownik przypisuje produkt/paragon do kategorii
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date_str = request.POST.get('date')

        if category_id and amount:
            category = get_object_or_404(Category, id=category_id)
            # Tworzymy oficjalną transakcję w bazie danych
            Transaction.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                description=description or "Wydatek z paragonu",
                date=date_str or date.today()
            )
            messages.success(request, f"Pomyślnie dodano wydatek '{description}' do kategorii {category.name}!")
            return redirect('receipt_list')

    # 4. Przetwarzamy tekst OCR na linijki, aby ładnie wyświetlić produkty w HTML
    processed_receipts = []
    for r in receipts:
        lines = [line.strip() for line in r.extracted_text.split('\n') if line.strip()] if r.extracted_text else []
        processed_receipts.append({
            'object': r,
            'lines': lines
        })

    return render(request, 'finance/receipt_list.html', {
        'receipts': processed_receipts,
        'categories': categories,
    })


@login_required
def receipt_delete(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk, user=request.user)
    if request.method == 'POST':
        receipt.delete()
        messages.success(request, "Paragon został usunięty z listy.")
    return redirect('receipt_list')