# Centus - Aplikacja do Zarządzania Budżetem Domowym

Aplikacja webowa stworzona w frameworku Django, służąca do śledzenia finansów osobistych, analizowania wydatków oraz planowania budżetu. Projekt pozwala na kontrolowanie przepływów finansowych, wizualizację danych oraz otrzymywanie rekomendacji oszczędnościowych.

##  Struktura Projektu

* **`core/`** – Katalog konfiguracyjny projektu Django.
    * `settings.py`: Główne ustawienia (baza danych, zainstalowane aplikacje, klucze).
    * `urls.py`: Główny routing adresów URL.
    * `wsgi.py` / `asgi.py`: Punkty wejścia dla serwerów WWW.

* **`finance/`** – Główna aplikacja zawierająca logikę biznesową.
    * `models.py`: Modele danych (Transakcje, Kategorie, Limity, Subskrypcje).
    * `views.py`: Logika sterująca widokami i przetwarzaniem danych.
    * `forms.py`: Formularze Django (walidacja danych wejściowych).
    * `recommendations.py`: Logika generowania porad finansowych.

* **`templates/`** – Pliki HTML.
    * `base.html`: Szablon bazowy z nawigacją i stopką.
    * `finance/`: Szablony widoków aplikacji finansowej.
    * `registration/`: Szablony logowania i rejestracji.

* **Pliki w katalogu głównym:**
    * `manage.py`: Skrypt do zarządzania projektem (uruchamianie, migracje).
    * `requirements.txt`: Lista wymaganych bibliotek Python.
    * `.env`: Plik ze zmiennymi środowiskowymi i kluczami.

---

## Instrukcja Uruchomienia

Aby uruchomić projekt na lokalnym komputerze, postępuj zgodnie z poniższymi krokami.

### 1. Klonowanie i przygotowanie środowiska

Pobierz projekt, a następnie w katalogu głównym utwórz wirtualne środowisko Python:

```bash
python -m venv venv
venv\Scripts\activate
```
### 2. Instalacja zależności
Zainstaluj wszystkie wymagane biblioteki z pliku requirements.txt:

``` bash
pip install -r requirements.txt
```

### 3. Migracja bazy danych
Utwórz tabele w bazie danych:

```Bash
python manage.py migrate
```
### 4. Uruchomienie serwera
Uruchom lokalny serwer deweloperski:

```Bash
python manage.py runserver
```
Aplikacja będzie dostępna pod adresem widocznym w terminalu.