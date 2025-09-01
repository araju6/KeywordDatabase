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

    def extract_paragraphs_and_refs(self):
        for script in self.soup(["script", "style"]):
            script.decompose()

        paragraphs = []
        global_refs = []
        para_with_citations = []

        citation_pattern = re.compile(r"\[(\d+)\]|\(([^)]+, \d{4})\)|doi:\s*\S+")

        for i, p in enumerate(self.soup.find_all("p")):
            text = p.get_text(" ", strip=True)
            refs = []

            # collect explicit <a> refs
            for a in p.find_all("a", href=True):
                anchor = a.get_text(" ", strip=True)
                href = a["href"]
                ref_entry = {"anchor": anchor, "href": href}
                refs.append(ref_entry)
                global_refs.append(ref_entry)

            if text:
                para_entry = {"id": i + 1, "text": text, "references": refs}
                paragraphs.append(para_entry)

                # check inline citations
                citations = citation_pattern.findall(text)
                if citations:
                    para_with_citations.append({
                        "id": i + 1,
                        "text": text,
                        "citations": ["".join(c).strip() for c in citations if "".join(c).strip()]
                    })

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

        return paragraphs, global_refs, para_with_citations, explicit_refs

    def run(self):
        self.fetch()
        meta = self.extract_metadata()
        paragraphs, global_refs, para_with_citations, explicit_refs = self.extract_paragraphs_and_refs()

        result = {
            "metadata": meta,
            "paragraphs": paragraphs,
            "paragraphs_with_citations": para_with_citations,
            "explicit_references": explicit_refs,
            "global_references": global_refs,
        }
        return result


if __name__ == "__main__":
    url = "https://www.broadinstitute.org/what-broad/areas-focus/project-spotlight/crispr-timeline"
    extractor = WebPageExtractor(url)
    data = extractor.run()

    print("=== METADATA ===")
    print(data["metadata"])

    print("\n=== FIRST 2 PARAGRAPHS ===")
    for para in data["paragraphs"][:2]:
        print(para)

    print("\n=== PARAGRAPHS WITH INLINE CITATIONS (first 2) ===")
    for para in data["paragraphs_with_citations"][:2]:
        print(para)

    print("\n=== EXPLICIT REFERENCES (first 5) ===")
    for ref in data["explicit_references"][:5]:
        print(ref)

    print("\n=== GLOBAL REFERENCES (first 5) ===")
    for ref in data["global_references"][:5]:
        print(ref)
