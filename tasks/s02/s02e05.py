import base64
from io import BytesIO
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from html_to_markdown import convert_to_markdown
import os
import re
load_dotenv()
client: OpenAI = OpenAI()

if not os.path.exists(os.path.join('data','s02e05','draft.md')):
    base_url = "https://c3ntrala.ag3nts.org/dane"
    png_pattern = r"\(i/.+\.png\)"
    mp3_pattern = r"\(i/.+\.mp3\)"

    html = requests.get(f"{base_url}/arxiv-draft.html")
    result = convert_to_markdown(html.text)

    png_files = re.findall(png_pattern, result)
    mp3_file = re.findall(mp3_pattern, result)[0]

    for file in png_files:
        img = requests.get(f"{base_url}/{file[1:-1]}")
        img_base64 = base64.b64encode(img.content).decode("utf-8")
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": "Zidentyfikuj obiekty i miejsca na obrazie. Zwróc tylko i wyłącznie opis po polsku.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{img_base64}",
                        }
                    ],
                },
            ],
        )
        result = result.replace(file, "\n"+response.output_text)

    mp3_response = requests.get(f"{base_url}/{mp3_file[1:-1]}")

    audio_file = BytesIO(mp3_response.content)
    audio_file.name = "audio.mp3"

    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        response_format="text"
    )

    result = result.replace(mp3_file, transcription, 1)
    print(result)
    with open(os.path.join('data','s02e05','draft.md'), "w", encoding="utf-8") as f:
        f.write(result)
else:
    with open(os.path.join('data','s02e05','draft.md'), "r", encoding="utf-8") as f:
        result = f.read()

url_centrala_questions: str = f"https://c3ntrala.ag3nts.org/data/{os.getenv("CENTRALA_API_KEY")}/arxiv.txt"
url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"

system_prompt = f"""
Jesteś asystentem do odpowiadania na pytania zgodnie z danymi w podanym źródle. Twoim zadaniem jest analiza tekstu źródłowego i opowiedź na pytania zgodnie z danymi zawartymi w tekście oraz zgodnie z podanym niżej formatem oraz wskazówkami.

Format odpowiedzi:
{{
        "01": "krótka odpowiedź w 1 zdaniu",
        "02": "krótka odpowiedź w 1 zdaniu",
        "03": "krótka odpowiedź w 1 zdaniu",
        [...]
}}

Wskazówki:
- Odpowiedź "Podczas pierwszej próby transmisji materii w czasie użyto owocu." na pytanie 01 NIE JEST POPRAWNĄ ODPOWIEDZIĄ, NIE UŻYWAJ JEJ.

Tekst źródłowy:
{result}
"""
questions = requests.get(url_centrala_questions).text
print(questions)
response_llm = client.responses.create(
    model="gpt-4o",
    input=[
        { "role" : "system", "content" : system_prompt },
        { "role" : "user", "content" : questions }
    ]
)

print('Response from LLM:', response_llm.output_text)

result_dict: dict = {
  "task": "arxiv",
  "apikey": os.getenv("CENTRALA_API_KEY"),
  "answer": json.loads(response_llm.output_text)
}

response: requests.Response = requests.post(url_centrala_report, json=result_dict, headers={'accept': 'application/json','Content-Type': 'application/json'})
print('Response from Centrala:', response.text)