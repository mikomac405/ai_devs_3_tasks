import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
import json
import unidecode

load_dotenv()
client = OpenAI()

URL_CENTRALA = "https://c3ntrala.ag3nts.org/report"
URL_PLACES = "https://c3ntrala.ag3nts.org/places"
URL_PEOPLE = "https://c3ntrala.ag3nts.org/people"

# system_prompt = """
# Wyciągnij z notatki miasta i wspomniane osoby.
# Wynik zwróć w postaci:
# {
#     "osoby" : ["osoba1", "osoba2", "osobaN", ...],
#     "miasta" : ["miasto1", "miasto2", "miastoN", ...],
# }
# """

# response_llm = client.responses.create(
#     model="gpt-5-mini-2025-08-07",
#     input=[
#         {"role": "system", "content": system_prompt},
#         {
#             "role": "user",
#             "content": """
#                 Podczas pobytu w Krakowie w 2019 roku, Barbara Zawadzka poznała swojego ówczesnego narzeczonego, a obecnie męża, Aleksandra Ragowskiego. Tam też poznali osobę prawdopodobnie powiązaną z ruchem oporu, której dane nie są nam znane. Istnieje podejrzenie, że już wtedy pracowali oni nad planami ograniczenia rozwoju sztucznej inteligencji, tłumacząc to względami bezpieczeństwa. Tajemniczy osobnik zajmował się także organizacją spotkań mających na celu podnoszenie wiedzy na temat wykorzystania sztucznej inteligencji przez programistów. Na spotkania te uczęszczała także Barbara.
#                 W okolicach 2021 roku Ragowski udał się do Warszawy celem spotkania z profesorem Andrzejem Majem. Prawdopodobnie nie zabrał ze sobą żony, a cel ich spotkania nie jest do końca jasny.
#                 Podczas pobytu w Warszawie, w instytucie profesora doszło do incydentu, w wyniku którego, jeden z laborantów - Rafał Bomba - zaginął. Niepotwierdzone źródła informacji podają jednak, że Rafał spędził około 2 lata, wynajmując pokój w pewnym hotelu. Dlaczego zniknął?  Przed kim się ukrywał? Z kim kontaktował się przez ten czas i dlaczego ujawnił się po tym czasie? Na te pytania nie znamy odpowiedzi, ale agenci starają się uzupełnić brakujące informacje.
#                 Istnieje podejrzenie, że Rafał mógł być powiązany z ruchem oporu. Prawdopodobnie przekazał on notatki profesora Maja w ręce Ragowskiego, a ten po powrocie do Krakowa mógł przekazać je swojej żonie. Z tego powodu uwaga naszej jednostki skupia się na odnalezieniu Barbary.
#                 Aktualne miejsce pobytu Barbary Zawadzkiej nie jest znane. Przypuszczamy jednak, że nie opuściła ona kraju.
#             """,
#         },
#     ],
# )

# data = json.loads(response_llm.output_text)
data = {
    "osoby": ["Barbara Zawadzka", "Aleksander Ragowski", "Andrzej Maj", "Rafał Bomba"],
    "miasta": ["Kraków", "Warszawa"],
}

for i in range(len(data["osoby"])):
    data["osoby"][i] = unidecode.unidecode(data["osoby"][i].split(" ")[0].upper())

for i in range(len(data["miasta"])):
    data["miasta"][i] = unidecode.unidecode(data["miasta"][i].split(" ")[0].upper())

data["osoby"].remove("BARBARA")


def query(s):
    return {"apikey": os.getenv("CENTRALA_API_KEY"), "query": s}


answer = None

while True:
    print(data["osoby"])

    for p in data["osoby"]:
        response = requests.post(
            URL_PEOPLE,
            json=query(p),
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )

        data["miasta"] += unidecode.unidecode(response.json()["message"]).split(" ")

    data["miasta"] = list(set(data["miasta"]))
    data["osoby"] = []

    print(data["miasta"])
    for c in data["miasta"]:
        if c == "LUBLIN":
            continue
        response = requests.post(
            URL_PLACES,
            json=query(c),
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )

        people = unidecode.unidecode(response.json()["message"]).split(" ")

        if c != "KRAKOW" and "BARBARA" in people:
            answer = c

        if "BARBARA" in people:
            people.remove("BARBARA")

        if people:
            data["osoby"] += people

    data["osoby"] = list(set(data["osoby"]))
    data["miasta"] = []

    print("=" * 50)
    if answer:
        break

response = requests.post(
    URL_CENTRALA,
    json={
        "task": "loop",
        "apikey": os.getenv("CENTRALA_API_KEY"),
        "answer": answer,
    },
    headers={"accept": "application/json", "Content-Type": "application/json"},
)

print(response.text)
