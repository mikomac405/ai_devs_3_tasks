import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

url_centrala_dane: str = f"https://c3ntrala.ag3nts.org/data/{os.getenv("CENTRALA_API_KEY")}/json.txt"
url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"

if not os.path.exists("data/json.txt"):
    with open("data/s01e03/json.txt", mode="wb") as f:
        f.write(requests.get(url_centrala_dane).content)

with open('data/s01e03/json.txt', 'r') as file:
    json_data: dict = json.load(file)

questions: list = []

json_data['apikey'] = os.getenv("CENTRALA_API_KEY")
for object in json_data['test-data']:
    a, b = object['question'].split(" + ")
    if object['answer'] != int(a) + int(b):
        object['answer'] = int(a) + int(b)
    if 'test' in object:
        questions.append(object['test'])

print("Questions for LLM:\n", questions, '\n')

system_prompt: str = """
Jesteś asystentem uzupełniającym odpowiedzi na pytania po angielsku. Twoim zadaniem jest uzupełnienie TYLKO odpowiedzi w jezyku angielskim na pytania w podanym formacie.

Format wejścia:
- [{"q": "{pytanie}", "a": "???"}]

Format wyjścia:
- [{"q": "{pytanie}", "a": "{odpowiedź}"}]

Zasady:
- Podmieniaj Zwracaj TYLKO odpowiedź (bez dodatkowych wyjaśnień czy kontekstu)
- W odpowiedzi zawsze używaj " zamiast '

Przykłady:
Wejście: [{"q": "What is the capital city of England", "a": "???"}, {"q": "name of the biggest country in the world", "a": "???"}]
Odpowiedź: [{"q": "What is the capital city of England", "a": "London"}, {"q": "name of the biggest country in the world", "a": "Russia"}]
"""

client: OpenAI = OpenAI()

response_llm = client.responses.create(
    model="o4-mini",
    input=[
        { "role" : "system", "content" : system_prompt },
        { "role" : "user", "content" : str(questions) }
    ]
)

print("Corrected questions from LLM:\n", response_llm.output_text, '\n')
answers: dict = json.loads(response_llm.output_text)

for object in json_data['test-data']:
    if 'test' in object:
        for answer in answers:
            if object['test']['q'] == answer['q']:
                object['test'] = answer

result: dict = {
  "task": "JSON",
  "apikey": os.getenv("CENTRALA_API_KEY"),
  "answer": json_data
}

response: requests.Response = requests.post(url_centrala_report, json=result, headers={'accept': 'application/json','Content-Type': 'application/json'})
print('Response from Centrala:', response.text)
