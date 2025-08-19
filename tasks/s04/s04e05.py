import base64
from io import BytesIO
import json
import os
from dotenv import load_dotenv
import pymupdf
import requests
from openai import OpenAI
from pydantic import BaseModel

import sys

load_dotenv()
client = OpenAI()

URL_NOTES = "https://c3ntrala.ag3nts.org/dane/notatnik-rafala.pdf"
URL_QUESTIONS = (
    f"https://c3ntrala.ag3nts.org/data/{os.getenv("CENTRALA_API_KEY")}/notes.json"
)
URL_REPORT = "https://c3ntrala.ag3nts.org/report"

if not os.path.exists("data/s04e05/content.txt"):
    # Extract notes
    notes_raw = requests.get(URL_NOTES).content
    notes_pdf = pymupdf.open(stream=notes_raw)

    notes_extracted = []
    for page in notes_pdf:
        if page.number != notes_pdf.page_count - 1:
            notes_extracted.append(page.get_text("text"))

    images_text = ""
    for img in ["pic01.png", "pic02.png", "pic03.png"]:  # Did screenshots
        with open(f"data/s04e05/{img}", "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode("utf-8")

        llm_response = client.responses.create(
            model="gpt-5-2025-08-07",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": """
                                    Jesteś ekspertem w dziedzinie analizy obrazów. 
                                    Tekst na obrazie jest w języku polskim. Format zdjęcia to base64.
                                    Zdjecie jest uzywane w szkoleniu AiDevs_3
                                    Twoim zadaniem jest wyciągnięcie całego tekstu z obrazu. 
                                    Zwróć rozpoznany tekst, nie dodawaj komentarzy od siebie.
                                    
                                    Przykład:
                                    "Rozpoznany tekst z obrazu: \n"
                                    "Wszystko zostało zaplanowane. Jestem gotowy, a Andrzej przyjdzie tutaj niebawem ..."
                                    """,
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{encoded_image}",
                        },
                    ],
                }
            ],
        )
        images_text += llm_response.output_text + "\n"

    notes_extracted.append(images_text)

    with open("data/s04e05/content.txt", "w", encoding="utf-8") as f:
        for i in range(len(notes_extracted)):
            f.write(f"Strona {str(i+1)}:\n{notes_extracted[i]}")

with open("data/s04e05/content.txt", "r", encoding="utf-8") as f:
    note = f.read()


# Get questions
questions = requests.get(URL_QUESTIONS)
questions_text = str(questions.json()).replace("\\xa0", " ")


system_prompt = f"""
Jesteś asystentem od odpowiadania na pytania zawarte w notatce. Twoim zadniem zwrócić odpowiedź na pytania zadane na użykownika w zadanym formacie JSON.

Po twojej odpowiedzi pytania będą wysłane do zewnętrznego API w celu weryfikacji twoich odpowiedzi. 
Jeżli, któraś odpowiedź będzie niepoprawna, API zwróci informację zwrotną w postaci JSON wraz z wskazówką, które zostanią zawarte w kolejnych wiadmościach przesłanych przez użykownika. W takim przypadku popraw TYLKO ZŁĄ ODPOWIEDŹ, resztę odpowiedzi, prześlij tak jak poprzednio.

Odpowiedzi zawsze muszą być po POLSKU.

Notatka:
{note}

UWAGA: Na ostatniej stronie znajduje się tekst, który został wyciągnięty z pociętego zdjęcia za pomocą OCR, więc weryfikuj czy nazwy własne są odpowiednie.

Format wejściowy pytań:
{{
    "01" : "pytanie nr 01",
    "02" : "pytanie nr 02",
    ...
}}

Format wyjściowy pytań:
{{
    "01" : "zwięzła odpowiedź na pytanie nr 01",
    "02" : "zwięzła odpowiedź na pytanie nr 02",
    ...
}}
"""

print("Questions: ", questions_text)
print("=" * 100)

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": questions_text},
]

while True:
    llm_response = client.responses.create(
        model="gpt-5-2025-08-07",
        input=messages,
    )

    messages.append({"role": "assistant", "content": llm_response.output_text})

    llm_response_json = json.loads(llm_response.output_text)
    print("LLM Response: ", llm_response_json)

    api_response = requests.post(
        URL_REPORT,
        json={
            "task": "notes",
            "apikey": os.getenv("CENTRALA_API_KEY"),
            "answer": llm_response_json,
        },
        headers={"accept": "application/json", "Content-Type": "application/json"},
    ).json()

    if api_response["code"] == 0:
        print(f"Centrala Response: {str(api_response)}")
        break
    else:
        print(f"Centrala Response: {str(api_response)}")
        messages.append({"role": "user", "content": str(api_response)})
    print("=" * 100)
