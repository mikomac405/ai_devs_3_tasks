import re
import requests
import html2text
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
URL_CENTRALA = "https://c3ntrala.ag3nts.org/report"


class WebSearchAgent:
    def __init__(self, base_url="https://softo.ag3nts.org"):
        self.client = OpenAI()
        self.base_url = base_url
        self.cached_sites = {}

        # Configure html2text
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0

    def get_page_content(self, url):
        """Fetch and convert HTML to markdown"""
        data = requests.get(url).text
        self.cached_sites[url] = self.html_converter.handle(data)

    def ask_llm(self, prompt):
        """Query OpenAI API"""
        pass

    def check_for_answer(self, page_content, question, available_links):
        """Check if page contains answer to question"""
        prompt = f"""
        Jesteś asystentem od znajdywania ZWIĘZŁEJ odpowiedzi w zawartości strony.
        Twoim zadaniem jest zapoznanie się z treścią pytania przesłanego przez użytkownika a następnie z zawartością strony w celu znalezienia odpowiedzi.
        
        Zawartość strony:
        {page_content}
        
        Jeśli możesz udzielić pełnej odpowiedzi to zwróć tylko tą odpowiedź w następującym formacie:
        ODPOWIEDŹ:zwięzła treść odpowiedzi jedno zdanie maks
        
        Bądź surowy, odpowiedź zwróć tylko wtedy, gdy jest wyraźnie widoczna w treści.
        
        Jeżeli nie możesz znaleźć odpowiedzi, to na podstawie treści pytania przeanalizuj poniżej podane dostępne linki i zdecyduj, który z nich najprawdopodobniej prowadzi do strony z odpowiedzią.

        Dostępne linki:
        {available_links}

        Link zwróć w formacie:
        LINK:https://softo.ag3nts.org/przykladowy_link

        Podsumowując:
        Jeżeli znajdziesz odpowiedź na pytanie na stronie to zwróć ją w odpowiednim formacie, a jeżeli jej nie znajdziesz to wskaż link, który najprawdopodobniej prowadzi do strony z odpowiedzią i zwróć go w odpowiednim formacie.
        """

        response_llm = self.client.responses.create(
            model="gpt-5-mini-2025-08-07",
            input=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {"role": "user", "content": question},
            ],
        )

        return response_llm.output_text

    def search_for_answer(
        self,
        question,
        current_url=None,
        max_depth=5,
        current_depth=0,
        visited_links=set(),
    ):
        """Main search logic"""
        if current_depth == max_depth:
            print("Max depth exceeded. Exit.")
            return None

        if current_url is None:
            current_url = self.base_url + "/"

        visited_links.add(current_url)

        if self.cached_sites.get(current_url) is None:
            self.get_page_content(current_url)

        site_data = self.cached_sites[current_url]

        links_on_site = set(
            [
                self.base_url + link
                for link in list(
                    set(
                        re.findall(
                            r'\[\s*[^\]]*?\s*\]\(\s*([^)\s]+)(?:\s+"[^"]*")?\s*\)',
                            site_data,
                        )
                    )
                )
            ]
        )

        llm_response = self.check_for_answer(
            site_data, question, list(links_on_site - visited_links)
        )
        if llm_response.startswith("ODPOWIEDŹ:"):
            answer = llm_response.removeprefix("ODPOWIEDŹ:")
            print(f"Question: {question} | Answer : {answer}")
            print()
            return answer
        elif llm_response.startswith("LINK:"):
            link = llm_response.removeprefix("LINK:")
            return self.search_for_answer(
                question, link, max_depth, current_depth + 1, visited_links
            )
        else:
            print("Something gone wrong. LLMs response:", llm_response)

    def search_questions(self, questions):
        """Process multiple questions"""
        answers = {}
        for q in questions:
            print(f"{q}:")
            answer = self.search_for_answer(questions[q])
            if answer:
                answers[q] = answer
            else:
                return None
        return answers


if __name__ == "__main__":
    agent = WebSearchAgent()

    questions = requests.get(
        f"https://c3ntrala.ag3nts.org/data/{os.getenv("CENTRALA_API_KEY")}/softo.json"
    ).json()

    answers = agent.search_questions(questions)
    if answers:
        response = requests.post(
            URL_CENTRALA,
            json={
                "task": "softo",
                "apikey": os.getenv("CENTRALA_API_KEY"),
                "answer": answers,
            },
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )


print(response.text)
