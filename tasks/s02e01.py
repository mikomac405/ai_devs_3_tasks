import requests
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"

client: OpenAI = OpenAI()

context: str = ""

if not os.path.exists(os.path.join("data/s02e01", "context.txt")):    
    for file in os.listdir("data/s02e01"):
        with open(os.path.join("data/s02e01", file), "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
            context += f"{file.split(".")[0].capitalize()}:\n"
            context += transcription
            context += "\n"

    with open(os.path.join("data/s02e01", "context.txt"), "w", encoding="utf-8") as f:
        f.write(context)

with open(os.path.join("data/s02e01", "context.txt"), "r", encoding="utf-8") as f:
    context = f.read()

system_prompt: str =f"""
    Jesteś asystentem od wyszukiwania informacji w kontekście. Na podstawie wskazówek z promptu oraz kontekście musisz wyszukać lub wydedukować i zwrócić TYLKO TE informacje, o które jesteś pytany.

    KONTEKST:
    {context}
"""

question = """
    Na jakiej ulicy znajduje się KONKRETNY INSTYTUT uczelni, gdzie wykłada profesor Andrzej Maj?
    Zwróć tylko nazwę ulicy.
    Analizuj kontekst, wyciągaj wnioski oraz wykorzystaj swoją wiedzę na temat omawianej uczelni aby zdobyć tę informację. 
"""

response_llm = client.responses.create(
    model="o4-mini",
    input=[
        { "role" : "system", "content" : system_prompt },
        { "role" : "user", "content" : question }
    ]
)

print("Response from LLM:", response_llm.output_text)

result: dict = {
  "task": "mp3",
  "apikey": os.getenv("CENTRALA_API_KEY"),
  "answer": response_llm.output_text
}

response: requests.Response = requests.post(url_centrala_report, json=result, headers={'accept': 'application/json','Content-Type': 'application/json'})
print('Response from Centrala:', response.text)