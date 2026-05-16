import os
from decimal import Decimal
from PIL import Image
import google.generativeai as genai
from pydantic import BaseModel, Field
from django.conf import settings
from .models import Category, Receipt, Transaction
from datetime import datetime


# 1. Definicja struktury, jaką MUSI zwrócić Gemini
class ReceiptAnalysisResult(BaseModel):
    extracted_text: str = Field(description="Oryginalny tekst odczytany z paragonu.")
    total_amount: float = Field(description="Całkowita kwota do zapłaty (używaj kropki zamiast przecinka).")
    date: str = Field(description="Data zakupu odczytana z paragonu, BEZWZGLĘDNIE w formacie YYYY-MM-DD. Jeśli brak, zwróć pusty string.")
    description: str = Field(description="Krótki tytuł transakcji, np. 'Apteka - leki', 'Biedronka - spożywcze', 'Paliwo Orlen'.")
    suggested_category_name: str = Field(description="Nazwa kategorii najlepiej pasująca do zakupów.")
    transaction_type: str = Field(description="Typ transakcji: 'INCOME' lub 'EXPENSE'. Paragon to zawsze 'EXPENSE'.")
    justification: str = Field(description="Krótkie uzasadnienie wyboru AI.")


def configure_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Brak GOOGLE_API_KEY w zmiennych środowiskowych (.env).")
    genai.configure(api_key=api_key)


def analyze_receipt_image(image_path: str, system_categories: list[str]) -> ReceiptAnalysisResult | None:
    configure_gemini()
    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Błąd otwarcia pliku obrazu: {e}")
        return None

    categories_str = ", ".join(system_categories)

    prompt = f"""
    Przeanalizuj załączony obraz paragonu i wykonaj następujące kroki:
    1. Odczytaj i zapisz cały widoczny tekst.
    2. Znajdź kwotę całkowitą (np. SUMA, DO ZAPŁATY).
    3. Przypisz paragon do jednej z kategorii w systemie: [{categories_str}]. Jeśli żadna nie pasuje, wymyśl nową logiczną kategorię.
    """

    try:
        response = model.generate_content(
            [img, prompt],  # Wysyłamy obraz ORAZ tekst do modelu
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ReceiptAnalysisResult,
                temperature=0.1,
            ),
        )
        return ReceiptAnalysisResult.model_validate_json(response.text)
    except Exception as e:
        print(f"Błąd komunikacji z API Gemini: {e}")
        return None


def process_and_categorize_receipt(receipt: Receipt) -> Receipt | None:
    if not receipt.image or not receipt.image.path:
        return None

    existing_categories = list(Category.objects.values_list('name', flat=True))
    result = analyze_receipt_image(receipt.image.path, existing_categories)

    if not result:
        return None

    # Zgodnie z założeniem: jeśli kategoria od AI nie istnieje, tworzymy ją automatycznie!
    category, created = Category.objects.get_or_create(
        name=result.suggested_category_name,
        defaults={'type': result.transaction_type}
    )

    # Zapisujemy wszystkie sugestie od AI w modelu paragonu
    receipt.extracted_text = result.extracted_text
    receipt.suggested_amount = Decimal(str(result.total_amount))
    receipt.suggested_description = result.description
    receipt.suggested_category = category

    # Bezpieczne parsowanie daty z formatu YYYY-MM-DD
    if result.date:
        try:
            receipt.suggested_date = datetime.strptime(result.date, '%Y-%m-%d').date()
        except ValueError:
            receipt.suggested_date = None

    receipt.save()
    return receipt