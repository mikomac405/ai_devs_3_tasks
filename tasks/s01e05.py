import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

url_centrala_dane: str = (
    f"https://c3ntrala.ag3nts.org/data/{os.getenv("CENTRALA_API_KEY")}/cenzura.txt"
)
url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"


data_to_censor: str = requests.get(url_centrala_dane).text
print("Data to censor:", data_to_censor)

system_prompt: str = """
Jesteś asystentem cenzurującym dane wrażliwe w tekście. Twoim zadaniem jest podmienianie danych wrażliwych na słowo CENZURA.

Zasady:
- Dane wrażliwe:
    - Imię
    - Nazwisko
    - Miejsowość zamieszkania
    - Ulica zmieszkania
    - Numer budynku zamieszkania
    - Wiek
- Podmieniaj TYLKO wskazane dane wrażliwe
- Jeżeli dwie dane wrażliwe są obok siebie to zastąp je jednym słowem CENZURA

Przykład:
Wejście: Tożsamość podejrzanego: Michał Wiśniewski. Mieszka we Wrocławiu na ul. Słonecznej 20. Wiek: 30 lat.
Wyjście: Tożsamość podejrzanego: CENZURA. Mieszka we CENZURA na ul. CENZURA. Wiek: CENZURA lat.
"""

client: OpenAI = OpenAI()

response_llm = client.responses.create(
    model="o4-mini",
    input=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": data_to_censor},
    ],
)

print("Data censored by LLM:", response_llm.output_text)

result: dict = {
    "task": "CENZURA",
    "apikey": os.getenv("CENTRALA_API_KEY"),
    "answer": response_llm.output_text,
}

response: requests.Response = requests.post(
    url_centrala_report,
    json=result,
    headers={"accept": "application/json", "Content-Type": "application/json"},
)
print("Response from Centrala:", response.text)
