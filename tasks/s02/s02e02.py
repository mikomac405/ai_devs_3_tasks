from dotenv import load_dotenv
from openai import OpenAI
import os
import base64

load_dotenv()

system_prompt: str = """
Jesteś asystentem wskazującym miasto na podstawie KILKU zdjęć map. Twoim zadaniem jest zidentyfikowanie i zwrócenie nazwy miasta zgodnie z zasadami, możesz wypisać kilka miast jeżeli nie jesteś pewny.

Zasady:
- Jeden z czterech dostarczonych obrazów wskazuje na miasto inne niż pozostałe obrazy, zignoruj to zdjęcie.
- Zidentyfikuj nazw ulic, charakterystyczne obiektów (np. cmentarzy, kościołów, szkół) i układ urbanistyczny w celu znalezienia miasta.
- W poszukiwanym mieście również muszą się znajdować spichlerz i twierdza.
- Upewnij się, że lokacje oraz ulice, które rozpoznajesz na mapie, na pewno znajdują się w lokacjach przedstawionych na obrazie w mieście, które zamierzasz zwrócić jako odpowiedź.
"""

client: OpenAI = OpenAI()

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

images = []

for file in os.listdir("data/s02e02"):
    print(file)
    images.append({
        "type": "input_image",
        "image_url": f"data:image/jpeg;base64,{image_to_base64(os.path.join("data/s02e02/", file))}",
    })
    


 
response_llm = client.responses.create(
    model="gpt-4o",
    input=[
        { "role" : "system", "content" : system_prompt },
        { "role" : "user", "content" : images }
    ]
)

print(response_llm.output_text)