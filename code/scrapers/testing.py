import requests

BASE_URL = "https://api.openalex.org"

def get_concept_id(keyword):
    """Search OpenAlex concepts for a keyword and return the top concept ID + name."""
    url = f"{BASE_URL}/concepts"
    params = {"search": keyword, "per-page": 5}
    r = requests.get(url, params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None, None
    top = results[0]  # take the best match
    return top["id"].split("/")[-1], top["display_name"]


def get_oldest_papers_by_concept(concept_id, n=20):
    """Fetch the n oldest works linked to a given OpenAlex concept ID."""
    url = f"{BASE_URL}/works"
    params = {
        "filter": f"concepts.id:{concept_id}",
        "sort": "publication_year:asc",
        "per-page": n,
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    
    papers = []
    for work in results:
        papers.append({
            "title": work.get("title"),
            "year": work.get("publication_year"),
            "doi": work.get("doi"),
            "authors": [a["author"]["display_name"] for a in work.get("authorships", [])],
            "url": work.get("primary_location", {}).get("landing_page_url")
        })
    return papers


if __name__ == "__main__":
    keyword = "convolutional neural network"
    
    concept_id, concept_name = get_concept_id(keyword)
    if concept_id:
        print(f"Found concept: {concept_name} (ID={concept_id})\n")
        papers = get_oldest_papers_by_concept(concept_id, n=20)
        for i, p in enumerate(papers, 1):
            print(f"{i}. {p['title']} ({p['year']})")
            print(f"   Authors: {', '.join(p['authors'])}")
            print(f"   DOI: {p['doi']}")
            print(f"   URL: {p['url']}\n")
    else:
        print("No matching concept found.")
