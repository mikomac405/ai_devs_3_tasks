import base64
import requests
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import pickle

load_dotenv()
url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"

extracted_data = []

client: OpenAI = OpenAI()


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

if not os.path.exists(os.path.join('data','s02e04', 'data.pickle')):
    for file in os.listdir(os.path.join("data", "s02e04")):
        file_path = os.path.join("data", "s02e04", file)
        name, ext = os.path.splitext(file)
        match ext:
            case ".txt":
                with open(file_path, "r", encoding='utf-8') as f:
                    extracted_data.append((file, f.read()))
            case ".png":
                response = client.responses.create(
                    model="gpt-4o",
                    input=[
                        {
                            "role": "system",
                            "content": "Extract and return only text from image.",
                        },
                        {
                            "role": "user",
                            "content": [{
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{image_to_base64(file_path)}",
                            }],
                        },
                    ],
                )
                extracted_data.append((file, response.output_text))
            case ".mp3":
                with open(file_path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", file=f, response_format="text"
                    )
                    extracted_data.append((file, transcription))
    
    with open(os.path.join('data', 's02e04','data.pickle'), 'wb') as handle:
        pickle.dump(extracted_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

else:
    with open(os.path.join('data', 's02e04','data.pickle'), 'rb') as handle:
        extracted_data = pickle.load(handle)

system_prompt = """
Jesteś asystentem do kategoryzacji plików. Twoim zadaniem jest przypisanie do pliku kategorii na podstawie jego zawartości w zadanym formacie.

Zasady:
- Na podstawie podanego zdecyduj, czy dany plik zawiera informacje o:
    - Ludziach: Uwzględniaj tylko notatki zawierające informacje o schwytanych ludziach lub o śladach ich obecności.
    - Hardware: Usterki hardwarowe (nie software).
  Jeśli plik nie pasuje do żadnej z powyższych kategorii, pomiń go. Nie twórz żadnych dodatkowych kategorii.

- Odpowiedź zwróć w podanym formacie:
{
    "people": ["plik1.txt", "plik2.mp3", "plik3.png"],
    "hardware": ["plik4.txt", "plik5.png", "plik6.mp3"]
}
"""

input_prompt = ""

for data in extracted_data:
    input_prompt += f"{data[0]}:\n{data[1]}\n{20 * "="}\n"

response_llm = client.responses.create(
    model="o4-mini",
    input=[
        { "role" : "system", "content" : system_prompt },
        { "role" : "user", "content" : input_prompt }
    ]
)

print("Response from LLM:", response_llm.output_text)

result: dict = {
  "task": "kategorie",
  "apikey": os.getenv("CENTRALA_API_KEY"),
  "answer": json.loads(response_llm.output_text) 
}

response: requests.Response = requests.post(url_centrala_report, json=result, headers={'accept': 'application/json','Content-Type': 'application/json'})
print('Response from Centrala:', response.text)