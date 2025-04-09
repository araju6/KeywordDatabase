from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()
class TavilySearcher:
    def __init__(self):
        self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

        if not self.TAVILY_API_KEY:
            raise ValueError("Tavily API key not found")

        self.client = TavilyClient(api_key=self.TAVILY_API_KEY)

    def search_query(self, query):
        response = self.client.search(query=query, search_depth="basic", include_answer=True, max_results=5)        
        if response.get('answer'):
            answer = response['answer']
            # return self.extract_quoted_text(answer)
            return answer
        
        return "Could not extract paper title"
    
    def extract_quoted_text(self, text):
        if '"' in text:
            start = text.find('"')
            end = text.find('"', start + 1)
            if end != -1:
                return text[start+1:end]
        return None

if __name__ == "__main__":
    searcher = TavilySearcher()
    term = "Convolutional Neural Networks"
    topic = "Computer Science"
    query = f"Which foundational research papers were responsible for inventing/discovering Convolutional Neural Networks in Computer Science? Look for older, foundational papers."

    title = searcher.search_query(query)
    print(f"\nExtracted title: {title}")