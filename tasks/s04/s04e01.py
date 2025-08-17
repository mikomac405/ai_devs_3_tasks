from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import ast


def generate_description(client, photos_base_url, photos):
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "system",
                "content": """
                Na podstawie przesłanych zdjęć wygeneruj szczegółowy opis Barbary.

                UWAGI:
                - NIE każde zdjęcie przedstawia Barbarę, więc musisz znaleźć postać, która powtarza się na WIĘKSZOŚCI obrazów
                - Rysopis musi być w języku polskim
                """,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"{photos_base_url}{photo.replace('.PNG','-small.PNG')}",
                    }
                    for photo in photos
                ],
            },
        ],
    )
    return response.output_text


def score_photo(client, photo_url):
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "system",
                "content": """
                Oceń jaki rodzaj naprawy załączonego zdjęcia powinien zostać przeprowadzony: 
                - REPAIR (dla szumów/glitchy)
                - DARKEN (dla zbyt jasnych)
                - BRIGHTEN (dla zbyt ciemnych)
                - NONE (jeżeli uznasz, że zdjęcie jest dobrej jakości lub nie nadaje się do dalszej obróbki)

                W odpowiedzi napisz TYLKO I WYŁĄCZNIE rodzaj naprawy.
                """,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"{photo_url}",
                    }
                ],
            },
        ],
    )
    return response.output_text


def extract_photos(client, text):
    response_llm = client.responses.create(
        model="o4-mini",
        input=[
            {
                "role": "system",
                "content": "Z podanego tekstu TYLKO wyciągnij i zwróć listę zdjęć podanych w tekście (podaj tylko nazwę pliku bez URL) w formacie: plik1.PNG,plik2.PNG,...",
            },
            {"role": "user", "content": text},
        ],
    )
    return response_llm.output_text.split(",")


def improve_photo(score, photo):
    result_dict = {
        "task": "photos",
        "apikey": os.getenv("CENTRALA_API_KEY"),
        "answer": f"{score} {photo}",
    }

    response: requests.Response = requests.post(
        url_centrala_report,
        json=result_dict,
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    return response.json()["message"]


if __name__ == "__main__":
    load_dotenv()
    url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"
    client = OpenAI()

    result_dict = {
        "task": "photos",
        "apikey": os.getenv("CENTRALA_API_KEY"),
        "answer": "START",
    }

    response: requests.Response = requests.post(
        url_centrala_report,
        json=result_dict,
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    text = response.json()["message"]
    print("Response from Centrala:", text)

    response_llm = client.responses.create(
        model="o4-mini",
        input=[
            {
                "role": "system",
                "content": "Z podanego tekstu TYLKO wyciągnij i zwróć JEDNO bazowe URL zdjęć, bez nazwy pliku",
            },
            {"role": "user", "content": text},
        ],
    )
    photos_base_url = response_llm.output_text.strip()
    photos = extract_photos(client, text)

    fixed_photos = []
    for photo in photos:
        while True:
            url = f"{photos_base_url}{photo.replace('.PNG','-small.PNG')}"
            print(url)
            score = score_photo(client, url)
            if score == "NONE":
                fixed_photos.append(photo)
                break

            photo = extract_photos(client, improve_photo(score, photo))[0]

    description = generate_description(client, photos_base_url, fixed_photos)
    print("Response from LLM:", description)

    result_dict = {
        "task": "photos",
        "apikey": os.getenv("CENTRALA_API_KEY"),
        "answer": description,
    }

    response: requests.Response = requests.post(
        url_centrala_report,
        json=result_dict,
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    text = response.json()["message"]
    print("Response from Centrala:", text)
