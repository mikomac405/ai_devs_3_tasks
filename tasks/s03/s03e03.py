import json
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

URL_CENTRALA_APIDB = "https://c3ntrala.ag3nts.org/apidb"
URL_CENTRALA = "https://c3ntrala.ag3nts.org/report"
SQL_STATEMENTS = ["SHOW CREATE TABLE datacenters;", "SHOW CREATE TABLE users;"]

sql_outputs = ""

for sql in SQL_STATEMENTS:
    req_json = {
        "task": "database",
        "apikey": os.getenv("CENTRALA_API_KEY"),
        "query": sql,
    }

    response = requests.post(
        URL_CENTRALA_APIDB,
        json=req_json,
        headers={"accept": "application/json", "Content-Type": "application/json"},
        timeout=30,
    )

    sql_outputs += response.text + "\n"

system_prompt = """
Twoim zadaniem jest napisanie zapytania SQL, które zwróci DC_ID aktywnych datacenter, których menadżerowie (z tabeli users) są nieaktywni na podstawie przekazanych struktur tabel.

Aktywne datacenter to takie, które ma pole "is_active" ustawiony na 1
Pole "manager" w tabeli datacenter ma do siebie przypisane numer "id" użytkownika z bazy users
Nieaktywny manager to taki, który ma pole "is_active" ustawiony na 0 i ma "access_level" ustawiony na "user"

Jako odpowiedź zwróć tylko i wyłącznie zapytanie SQL.
"""

response_llm = client.responses.create(
    model="gpt-5-mini-2025-08-07",
    input=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sql_outputs},
    ],
)

print("LLM: ", response_llm.output_text)

req_json = {
    "task": "database",
    "apikey": os.getenv("CENTRALA_API_KEY"),
    "query": response_llm.output_text,
}

response = requests.post(
    URL_CENTRALA_APIDB,
    json=req_json,
    headers={"accept": "application/json", "Content-Type": "application/json"},
    timeout=30,
)

data = response.json()
print("Centrala: ", response.text)

req_json = {
    "task": "database",
    "apikey": os.getenv("CENTRALA_API_KEY"),
    "answer": [x["dc_id"] for x in data["reply"]],
}

response = requests.post(
    URL_CENTRALA,
    json=req_json,
    headers={"accept": "application/json", "Content-Type": "application/json"},
    timeout=30,
)

print("Centrala: ", response.text)
