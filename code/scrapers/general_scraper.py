import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class WebPageExtractor:
    def __init__(self, url: str):
        self.url = url
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        self.html = None
        self.soup = None

    def fetch_requests(self):
        resp = requests.get(self.url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.text

    def fetch_playwright(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, timeout=30000)
            content = page.content()
            browser.close()
            return content

    def fetch(self):
        try:
            self.html = self.fetch_requests()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                print("⚠️ 403 Forbidden – retrying with Playwright...")
                self.html = self.fetch_playwright()
            else:
                raise e
        self.soup = BeautifulSoup(self.html, "html.parser")

    def extract_metadata(self):
        title = self.soup.title.string if self.soup.title else None
        desc_tag = self.soup.find("meta", attrs={"name": "description"}) or \
                   self.soup.find("meta", attrs={"property": "og:description"})
        description = desc_tag["content"] if desc_tag else None
        return {"title": title, "description": description, "url": self.url}

    def extract_content_and_refs(self):
        # remove scripts/styles
        for script in self.soup(["script", "style"]):
            script.decompose()

        # get all visible text as one block
        all_text = " ".join([p.get_text(" ", strip=True) for p in self.soup.find_all("p") if p.get_text(strip=True)])

        # extract all explicit <a> references
        global_refs = []
        for a in self.soup.find_all("a", href=True):
            anchor = a.get_text(" ", strip=True)
            href = a["href"]
            global_refs.append({"anchor": anchor, "href": href})

        # try to find a dedicated references section
        explicit_refs = []
        for header in self.soup.find_all(["h2", "h3", "h4", "strong", "b"]):
            if re.search(r"(references|bibliography|sources|works cited)", header.get_text().lower()):
                sibs = header.find_all_next(["p", "li", "div"])
                for s in sibs:
                    t = s.get_text(" ", strip=True)
                    if len(t) > 10:
                        explicit_refs.append(t)
                break

        return {
            "all_text": all_text,
            "explicit_references": explicit_refs,
            "global_references": global_refs
        }

    def run(self):
        self.fetch()
        meta = self.extract_metadata()
        content_and_refs = self.extract_content_and_refs()
        result = {
            "metadata": meta,
            **content_and_refs
        }
        return result


if __name__ == "__main__":
    url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC9377665/"
    extractor = WebPageExtractor(url)
    data = extractor.run()

    print("=== METADATA ===")
    print(data["metadata"])
    print("\n=== ALL TEXT ===")
    print(data["all_text"][:1000] + "...")  # print first 1000 chars

    print("\n=== EXPLICIT REFERENCES (first 5) ===")
    for ref in data["explicit_references"][:5]:
        print(ref)

    print("\n=== GLOBAL REFERENCES (first 5) ===")
    for ref in data["global_references"][:5]:
        print(ref)
