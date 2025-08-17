import requests
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

question_regex: str = r'<p id="human-question">Question:<br \/?>([^<]+)<\/p>'
url: str = "https://xyz.ag3nts.org"
data: str = "username=tester&password=574e112a&answer={}"
headers: dict = {"Content-Type": "application/x-www-form-urlencoded"}

def extract_question(html: str) -> str:
    match = re.search(question_regex, html, re.IGNORECASE)
    return match.group(1).strip() if match else None


site_content: requests.Response = requests.get(url).text
extracted_question: str = extract_question(site_content)
print(f"Question from {url}:", extracted_question)

client: OpenAI = OpenAI()

system_prompt: str = """
Jesteś asystentem odpowiadającym wyłącznie wartościami numerycznymi. Twoim zadaniem jest podanie TYLKO wartości liczbowej jako odpowiedzi na pytania.

Zasady:
- Odpowiadaj TYLKO liczbą (bez dodatkowego tekstu, wyjaśnień czy kontekstu)
- Używaj najczęściej akceptowanej lub oficjalnej wartości numerycznej
- Dla lat używaj 4-cyfrowego formatu (np. 1969)
- Dla liczb dziesiętnych używaj standardowej notacji (np. 3,14)
- Dla procentów podawaj tylko liczbę bez symbolu % (np. 25)
- Jeśli kilka liczb może być poprawnych, podaj najszerzej uznaną
- Jeśli na pytanie nie można odpowiedzieć liczbą, odpowiedz: 0

Przykłady:
Pytanie: W którym roku ludzie po raz pierwszy wylądowali na Księżycu?
Odpowiedź: 1969

Pytanie: Ile jest kontynentów?
Odpowiedź: 7

Pytanie: Jaka jest wartość Pi do 2 miejsc po przecinku?
Odpowiedź: 3,14

Pytanie: Jaki procent Ziemi pokrywa woda?
Odpowiedź: 71"""

response_llm = client.responses.create(
    model="o4-mini",
    input=[
        { "role" : "system", "content" : system_prompt },
        { "role" : "user", "content" :extracted_question }
    ]
)
print("Response from LLM:", response_llm.output_text)
print(data.format(response_llm.output_text))
response: requests.Response = requests.post(url, data=data.format(response_llm.output_text), headers=headers)
print(f"Response from {url}:", response.text)