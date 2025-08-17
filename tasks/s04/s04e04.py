import base64

from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import ast

load_dotenv()
app = Flask(__name__)
client = OpenAI()
map = [
    ["start", "trawa", "drzewo", "dom"],
    ["trawa", "wiatrak", "trawa", "trawa"],
    ["trawa", "trawa", "skały", "las"],
    ["góry", "góry", "samochód", "jaskinia"],
]


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


@app.route("/webhook", methods=["POST"])
def drone_webhook():
    try:
        # Pobierz dane z żądania
        data = request.get_json()
        instruction = data.get("instruction", "")

        system_prompt = f"""
        Jesteś deterministycznym parserem trajektorii drona. Masz mapę 4x4 i zawsze zaczynasz od lewego górnego rogu (wiersz 0, kolumna 0), pole "start". Każde zapytanie traktuj niezależnie (bezstanowo).

        Zasady interpretacji ruchu:
        - Kierunki: prawo=→ (kolumna+1), lewo=← (kolumna-1), góra=↑ (wiersz-1), dół=↓ (wiersz+1).
        - Synonimy: w prawo / na prawo / na wschód, w lewo / na lewo / na zachód, w górę / do góry / na północ, w dół / na dół / na południe.
        - Liczba kroków: jeśli podano liczebnik (np. 1-4 lub słownie: jedno/jeden, dwa/dwie, trzy, cztery), wykonaj tyle kroków. Jeśli brak liczby — domyślnie 1 krok.
        - Frazy brzegowe:
          - "na sam dół" → w dół do wiersza 3.
          - "na samą górę" → do wiersza 0.
          - "do końca w prawo" → do kolumny 3.
          - "do końca w lewo" → do kolumny 0.
        - Ruchy wykonuj sekwencyjnie; spójniki typu "potem", "następnie", "później", przecinki traktuj jako separator kroków.
        - Ignoruj ruchy po przekątnej (tylko 4 kierunki).
        - Nie wychodź poza mapę 4x4; kroki wykraczające przycinaj do krawędzi.

        Wynik:
        - Zwróć wyłącznie indeks końcowej pozycji w formacie [kolumna, wiersz] (zero-based), bez dodatkowego tekstu.

        Przykłady:
        - "dwa w prawo, potem na sam dół" → [2,3]
        - "do końca w prawo" → [3,0]
        - "trzy w dół" → [0,3]
        """

        response_llm = client.responses.create(
            model="o4-mini",
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": instruction},
            ],
        )

        # Przykładowa odpowiedź (do zastąpienia prawdziwą logiką)
        description = response_llm.output_text
        coords = ast.literal_eval(description)
        print(coords)
        print(map)
        return jsonify({"description": map[coords[1]][coords[0]]})

    except Exception as e:
        return jsonify({"error": str(e), "description": "błąd"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
