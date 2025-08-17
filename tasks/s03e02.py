import zipfile
import os
import re
from datetime import datetime
from openai import OpenAI
from typing import List, Dict
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

import requests

load_dotenv()
client = OpenAI()
url_centrala_report: str = "https://c3ntrala.ag3nts.org/report"


class ReportIndexer:
    def __init__(self, path: str, qdrant_url: str = "http://localhost:6333"):
        self.path = path
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = "Kluczowe"
        self.embedding_size = 1536  # rozmiar dla text-embedding-3-small

        self.create_collection()

    def create_collection(self):
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_size, distance=Distance.COSINE
                    ),
                )
                print(f"Utworzono kolekcję: {self.collection_name}")
            else:
                print(f"Kolekcja {self.collection_name} już istnieje")
        except Exception as e:
            print(f"Błąd podczas tworzenia kolekcji: {e}")

    def extract_date_from_filename(self, filename: str) -> str:
        """Wyciąga datę z nazwy pliku i formatuje do YYYY_MM_DD"""
        date_pattern = r"(\d{4}_\d{2}_\d{2})"
        match = re.search(date_pattern, filename)

        if match:
            return match.group(1)
        else:
            raise ValueError(f"Nie można wyodrębnić daty z nazwy pliku: {filename}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generuje embedding dla podanego tekstu"""
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding

    def process_files(self):
        points = []
        txt_files = [f for f in os.listdir(self.path) if f.endswith(".txt")]

        print(f"Znaleziono {len(txt_files)} plików raportów")

        for filename in txt_files:
            try:
                # Wyciągnij datę z nazwy pliku
                report_date = self.extract_date_from_filename(
                    os.path.join(self.path, filename)
                )

                # Odczytaj treść raportu
                with open(os.path.join(self.path, filename), encoding="utf-8") as file:
                    content = file.read()

                # Wygeneruj embedding
                embedding = self.generate_embedding(content)

                # Przygotuj punkt do Qdrant
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "date": report_date,
                        "filename": os.path.join(self.path, filename),
                        "content": content,
                        "content_length": len(content),
                    },
                )

                points.append(point)
                print(
                    f"Przygotowano: {os.path.join(self.path,filename)} (data: {report_date})"
                )

            except Exception as e:
                print(
                    f"Błąd podczas przetwarzania {os.path.join(self.path,filename)}: {e}"
                )

        # Wstaw wszystkie punkty do Qdrant
        if points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name, points=points
            )
            print(f"Zapisano {len(points)} embeddings do Qdrant")

    def search_by_date(self, target_date: str, limit: int = 10):
        """Wyszukuje raporty według daty"""
        search_result = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter={"must": [{"key": "date", "match": {"value": target_date}}]},
            limit=limit,
            with_payload=True,
        )

        return search_result[0]  # points

    def semantic_search(self, query: str, limit: int = 5):
        """Wyszukiwanie semantyczne w raportach"""
        query_embedding = self.generate_embedding(query)

        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True,
        )

        return search_result

    def get_collection_info(self):
        """Zwraca informacje o kolekcji"""
        return self.qdrant_client.get_collection(self.collection_name)


# Przykład użycia
if __name__ == "__main__":
    path = "data/s03e02/do-not-share"

    # Utwórz indekser (upewnij się, że Qdrant działa na localhost:6333)
    indexer = ReportIndexer(path)

    # Przetwórz pliki
    # indexer.process_files()

    # Pytanie do przeszukania
    question = (
        "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
    )

    # Wygeneruj embedding pytania
    print(f"Szukam odpowiedzi na pytanie: {question}")

    # Wyszukaj najbardziej pasujący raport (limit=1)
    search_results = indexer.semantic_search(question, limit=1)

    if search_results:
        best_match = search_results[0]
        report_date = best_match.payload["date"]
        filename = best_match.payload["filename"]
        score = best_match.score

        print(f"\nNajbardziej pasujący raport:")
        print(f"Data: {report_date}")
        print(f"Plik: {filename}")
        print(f"Score podobieństwa: {score:.3f}")

        # Wyświetl fragment treści dla weryfikacji
        content = best_match.payload["content"]
        print(f"\nFragment treści:")
        print(content[:500] + "..." if len(content) > 500 else content)

        # Odpowiedź na pytanie
        print(f"\nODPOWIEDŹ: {report_date}")

    else:
        print("Nie znaleziono pasujących raportów")

    # Dodatkowe wyszukiwanie z większą liczbą wyników dla porównania

    top_results = indexer.semantic_search(question, limit=1)

    for i, result in enumerate(top_results, 1):
        print(
            f"{i}. Response from LLM: Data: {result.payload['date']} | Score: {result.score:.3f} | {result.payload['filename']}"
        )

        result_dict: dict = {
            "task": "wektory",
            "apikey": os.getenv("CENTRALA_API_KEY"),
            "answer": result.payload["date"].replace("_", "-"),
        }

        response: requests.Response = requests.post(
            url_centrala_report,
            json=result_dict,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        print("Response from Centrala:", response.text)
