import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time
import re

class GoogleSearcher:
    def __init__(self, user_agent=None):
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def search_query(self, query, max_results=3):
        return list(search(query, num_results=max_results))

    def fetch_page_text(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return f"[Error {response.status_code}]: Unable to fetch {url}"
        except Exception as e:
            return f"[Exception]: {e}"

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav", "form", "noscript", "iframe", "aside"]):
            tag.decompose()
        main_content = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile("content|article|main", re.I)) or soup

        paragraphs = []
        for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']):
            text = p.get_text().strip()
            if text and len(text) > 15:
                paragraphs.append(text)

        if not paragraphs:
            text = main_content.get_text(separator="\n")
            lines = [line.strip() for line in text.splitlines()]
            paragraphs = [line for line in lines if line and len(line) > 15]

        visible_text = "\n\n".join(paragraphs)
        return re.sub(r'\n\s*\n', '\n\n', visible_text)

    def extract_meaningful_info(self, text):
        if not text or text.startswith("[Error") or text.startswith("[Exception"):
            return "Failed to extract content"

        paragraphs = text.split("\n\n")
        filtered_paragraphs = []
        for p in paragraphs:
            if re.search(r'cookie|privacy policy|terms of use|contact us|all rights reserved', p, re.I):
                continue
            if len(p.split()) < 8:
                continue
            filtered_paragraphs.append(p)

        if len(filtered_paragraphs) < 3 and len(paragraphs) > 3:
            filtered_paragraphs = [p for p in paragraphs if len(p.split()) >= 5]

        return "\n\n".join(filtered_paragraphs)

    def get_webpage_contents(self, query, max_results=3):
        print(f"Searching for: {query}")
        urls = self.search_query(query, max_results)

        if not urls:
            return [("No results found", "Search failed to return any valid URLs.")]

        page_contents = []
        for url in urls:
            print(f"Fetching content from: {url}")
            content = self.fetch_page_text(url)
            meaningful_content = self.extract_meaningful_info(content)
            page_contents.append((url, meaningful_content))
            time.sleep(2)

        return page_contents

    def extract_citation_blocks(self, text):
        citation_blocks = []
        matches = re.findall(r'(?m)^\^.*?(?=\n|$)', text)

        seen = set()
        for match in matches:
            clean = match.strip('^').strip()
            if clean and clean not in seen:
                citation_blocks.append(clean)
                seen.add(clean)

        return citation_blocks

    def find_wikipedia_page(self, keyword: str) -> str:
        """
        Find the Wikipedia page URL for a given keyword using Google search.
        
        Args:
            keyword: The keyword to search for
            
        Returns:
            The Wikipedia page URL if found, None otherwise
        """
        query = f"{keyword} site:wikipedia.org"
        try:
            print(f"Searching for Wikipedia page with query: {query}")
            results = self.search_query(query, max_results=1)
            print(f"Search results: {results}")
            if results and len(results) > 0:
                url = results[0]
                print(f"First result URL: {url}")
                # Verify it's a Wikipedia page
                if "wikipedia.org/wiki/" in url:
                    print(f"URL verified as Wikipedia page")
                    return url
                else:
                    print(f"URL does not contain 'wikipedia.org/wiki/'")
        except Exception as e:
            print(f"Error finding Wikipedia page: {e}")
        return None


if __name__ == "__main__":
    searcher = GoogleSearcher()
    term = "Convolutional Neural Networks"
    query = f"Which foundational research papers were responsible for inventing/discovering {term} in Computer Science?"

    results = searcher.get_webpage_contents(query)

    # print("\n\n=== MEANINGFUL INFORMATION EXTRACTED ===\n")
    # for i, (url, text) in enumerate(results):
    #     print(f"\n--- Result {i + 1}: {url} ---")
    #     print(text[:1500])
    #     print("\n" + "-"*80)

    citations = searcher.extract_citation_blocks(results[0][1])
    print("\n=== Citations Found ===\n")
    for i in range(len(citations)):
        print(i, citations[i])


