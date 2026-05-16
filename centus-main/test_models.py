import os
import google.generativeai as genai
from dotenv import load_dotenv

# Wczytujemy Twój klucz z pliku .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("🔍 Odpytuję serwery Google...")
print("-" * 40)
print("Dostępne modele wspierające generowanie treści (w tym Vision):")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ {m.name}")
except Exception as e:
    print(f"❌ Wystąpił błąd podczas pobierania listy: {e}")