import requests
import codecs
from dotenv import load_dotenv
from openai import OpenAI
import os
import json 

load_dotenv()

system_prompt: str = """
Jesteś asystentem generującym obraz robota na podstawie opisu. Twoim zadaniem jest wygenerowanie opisu robota zgodnie z dostarczoną specyfikacją.

Zasady:
- Nie pomijaj żadnych szczegółów opisu
- Dokładnie odwzoruj robota zgodnie z opisem
"""

url_centrala_robot: str = f"https://c3ntrala.ag3nts.org/data/{os.getenv("CENTRALA_API_KEY")}/robotid.json"
url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"

robot_desc: str = json.loads(codecs.decode(requests.get(url_centrala_robot).text, 'unicode_escape'))
print("Robot description:", robot_desc["description"])

client: OpenAI = OpenAI()
response_llm = client.images.generate(
    model="dall-e-3",
    prompt=robot_desc["description"]
)
print("DALL-E 3 generated image:",response_llm.data[0].url)

result: dict = {
  "task": "robotid",
  "apikey": os.getenv("CENTRALA_API_KEY"),
  "answer": response_llm.data[0].url
}

response: requests.Response = requests.post(url_centrala_report, json=result, headers={'accept': 'application/json','Content-Type': 'application/json'})
print('Response from Centrala:', response.text)