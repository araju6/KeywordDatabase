import requests

class ScholarRetriever:
    def __init__(self) -> None:
        pass
        
    def search_paper(self, title):
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={title}&fields=title,abstract,url,citationCount"
        response = requests.get(url)
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            first_result = data['data'][0]
            return {
                'url': first_result.get('url', 'No URL found'), 
                "abstract": first_result.get('abstract', 'No abstract found'), 
                "citations": first_result.get('citationCount', 0), 
                "title": first_result.get('title', 'No Title Found')
            }
        return {"url": None, "abstract": None, "citations": None, "title":None}

retriever = ScholarRetriever()
# paper_info = retriever.search_paper("Learning internal representations by error propogation")
# print(paper_info)
