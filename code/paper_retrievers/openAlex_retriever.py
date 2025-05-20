import requests
from bs4 import BeautifulSoup

class OpenAlexRetriever:
    def __init__(self) -> None:
        self.base_url = "https://api.openalex.org/works"
    
    def convert_inverted_index_to_text(self, inverted_index):
        if not inverted_index:
            return None
        max_position = 0
        for positions in inverted_index.values():
            if positions and max(positions) > max_position:
                max_position = max(positions)
        words = [""] * (max_position + 1)
        for word, positions in inverted_index.items():
            for position in positions:
                words[position] = word
        return " ".join(words)

    def scrape_abstract_from_webpage(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            abstract_div = soup.find('div', {'id': 'Abs1-content'})
            if abstract_div:
                return abstract_div.get_text(separator=" ", strip=True)

            return None
        except Exception as e:
            print(f"Error scraping abstract: {e}")
            return None

    def search_paper(self, title):
        url = f"{self.base_url}?filter=title.search:{title}"
        response = requests.get(url)
        data = response.json()
        
        if 'results' in data and len(data['results']) > 0:
            first_result = data['results'][0]
            landing_page = first_result.get('primary_location', {}).get('landing_page_url', None)
            abstract = self.convert_inverted_index_to_text(first_result.get('abstract_inverted_index', None))

            if not abstract and landing_page:
                abstract = self.scrape_abstract_from_webpage(landing_page)
            
            return {
                'url': first_result.get('doi', landing_page or 'No URL found'),
                'abstract': abstract or "No abstract found",
                'citations': first_result.get('cited_by_count', 0),
                'title': first_result.get('title', 'No Title Found')
            }
        return {"url": None, "abstract": None, "citations": None, "title": None}
    
    
retriever = OpenAlexRetriever()
paper_info = retriever.search_paper("Learning representations by back-propagating errors")
print(paper_info)
