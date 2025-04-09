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
        urls = list(search(query, num_results=max_results))
        return urls

    def fetch_page_text(self, url):
        response = requests.get(url, headers=self.headers, timeout=15)
        if response.status_code != 200:
            return f"[Error {response.status_code}]: Unable to fetch {url}"
            
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
        
        visible_text = re.sub(r'\n\s*\n', '\n\n', visible_text)
        
        return visible_text


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
        
        result = "\n\n".join(filtered_paragraphs)
        return result

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

if __name__ == "__main__":
    searcher = GoogleSearcher()
    term = "Convolutional Neural Networks"
    query = f"Which foundational research papers were responsible for inventing/discovering {term} in Computer Science?"
    
    results = searcher.get_webpage_contents(query)
    
    print("\n\n=== MEANINGFUL INFORMATION EXTRACTED ===\n")
    # for i, (url, text) in enumerate(results):
    #     print(f"\n--- Result {i + 1}: {url} ---")
    #     print(text[:1500])
    #     print("\n" + "-"*80)
    print(len(results[0]))