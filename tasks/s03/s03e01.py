import json
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

URL_CENTRALA = "https://c3ntrala.ag3nts.org/report"
FACTS_DIR = os.path.join("data", "s03e01", "facts")
REPORTS_DIR = os.path.join("data", "s03e01", "reports")

# --- 1) Wczytanie danych ---
fakty_source = []
for filename in sorted(os.listdir(FACTS_DIR)):
    if not filename.endswith(".txt"):
        continue
    with open(os.path.join(FACTS_DIR, filename), "r", encoding="utf-8") as f:
        fakty_source.append(f"{filename.replace('.txt','')}:\n{f.read()}\n")
fakty_source = "".join(fakty_source)

print("FAKTY:")
print(fakty_source)

reports_source = []
report_filenames = []
for filename in sorted(os.listdir(REPORTS_DIR)):
    if not filename.endswith(".txt"):
        continue
    report_filenames.append(filename)
    with open(os.path.join(REPORTS_DIR, filename), "r", encoding="utf-8") as f:
        reports_source.append(f"{filename}: {f.read()}\n")
reports_source = "".join(reports_source)

print("RAPORTY:")
print(reports_source)

system_prompt = f"""
Zapoznaj się z zawartością tekstu. Tekst zawiera 10 raportów. Dla każdego z 10 raportów:
    - Przeanalizuj treść raportu. Zidentyfikuj kluczowe informacje: co się stało, gdzie, kto był zaangażowany, jakie przedmioty/technologie się pojawiły.
    - Przeanalizuj fakty z sekcji "Fakty o fabryce" poniżej. Znajdź fakty powiązane z aktualnie przetwarzanym raportem. Najczęstszym łącznikiem będą osoby wymienione w raporcie i w faktach.
    - Wykorzystaj także informacje z nazwy pliku raportu.
    - Wygeneruj listę słów kluczowych.
    - Słowa kluczowe muszą być w języku polskim.
    - Muszą być w mianowniku (np. "nauczyciel", "programista", a nie "nauczyciela", "programistów"). 
    - Słowa powinny być oddzielone przecinkami (np. słowo1,słowo2,słowo3).
    - Lista powinna precyzyjnie opisywać raport, uwzględniając treść raportu, powiązane fakty oraz informacje z nazwy pliku.
    - Słów kluczowych może być dowolnie wiele dla danego raportu. 
    
Fakty o fabryce
{fakty_source} 
*koniec faktów* 

Przygotuj odpowiedź w formacie JSON. Zobacz sekcję "Format odpowiedzi" poniżej.

Format odpowiedzi
Twoje rozwiązanie musi być obiektem JSON, gdzie kluczami są pełne nazwy plików raportów, a wartościami są stringi zawierające słowa kluczowe oddzielone przecinkami.
Odpowiedź musi zawierać dokładnie 10 wpisów (po jednym wpisie zawierającym wiele słów klczowych dla każdego z analizowanych raportów). Słów kluczowych może być dowolnie wiele dla danego raportu.
Na początku każdego raportu znajduje się nazwa pliku, z którego pochodzi. Użyj jej w formacie odpowiedzi tak jak pokazano w przykładzie:
{{
    "task": "dokumenty",
    "apikey": "YOUR_API_KEY",
    "answer": {{ 
        "2024-11-12_report-00-sektor_C4.txt": "słowo,kluczowe,przykład1",
        "2024-11-12_report-01-sektor_A1.txt": "inne,słowa,przykład2"
    }}
}}
"""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": reports_source},
]

# --- 4) Pętla z obsługą feedbacku z Centrali ---
MAX_TRIES = 5
for attempt in range(1, MAX_TRIES + 1):
    response_llm = client.responses.create(
        model="gpt-5-mini-2025-08-07", input=messages
    )
    assistant_json_text = response_llm.output_text
    try:
        print("LLM:", assistant_json_text)
        response_obj = json.loads(assistant_json_text)
    except json.JSONDecodeError:
        print("Wrong json")
        # Jeśli model zwróci niepoprawny JSON, poproś o poprawkę
        messages.append({"role": "assistant", "content": assistant_json_text})
        messages.append(
            {"role": "user", "content": "Popraw odpowiedź. Zwróć poprawny JSON."}
        )
        continue

    response_obj["apikey"] = os.getenv("CENTRALA_API_KEY", "")

    http = requests.post(
        URL_CENTRALA,
        json=response_obj,
        headers={"accept": "application/json", "Content-Type": "application/json"},
        timeout=30,
    )

    print("Centrala:", f"[{http.status_code}] {http.text}")
    print("=" * 100)

    if http.status_code == 200:
        break

    # --- Dodanie feedbacku jako kolejna wiadomość usera ---
    messages.append({"role": "assistant", "content": assistant_json_text})
    messages.append({"role": "user", "content": http.text})
else:
    raise SystemExit("Nie udało się uzyskać poprawnej odpowiedzi po kilku próbach.")
