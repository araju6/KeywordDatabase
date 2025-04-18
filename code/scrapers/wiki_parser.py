import requests
from bs4 import BeautifulSoup
import re

class WikipediaParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def extract_page_soup(self, full_url):
        """Fetches URL and returns a parsed BeautifulSoup object, or None on error."""
        try:
            print(f"Fetching URL: {full_url}")
            resp = self.session.get(full_url)
            resp.raise_for_status()
            print("Successfully fetched page.")
            return BeautifulSoup(resp.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return None
    
    def extract_references(self, full_url):
        try:
            print(f"Fetching URL: {full_url}")
            resp = self.session.get(full_url)
            resp.raise_for_status()
            print("Successfully fetched page.")
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during fetch: {e}")
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')

        container = (soup.select_one('div.reflist-columns')
                     or soup.select_one('div.reflist')
                     or soup.select_one('ol.references'))

        if not container:
            print("Could not find references container (div.reflist or ol.references).")
            ol_blocks = soup.find_all('ol', class_='references')
            if not ol_blocks:
                 print("Could not find any <ol class='references'>.")
                 return []
            print("Warning: Found <ol class='references'> outside standard containers.")
        else:
             ol_blocks = container.select('ol.references')
             if container.name == 'ol' and 'references' in container.get('class', []):
                 ol_blocks = [container]
             elif not ol_blocks:
                 print(f"Found container '{container.name}.{'.'.join(container.get('class',[]))}', but no <ol class='references'> inside.")
                 return []

        refs = {}
        current_ref_number = 1

        for ol in ol_blocks:
            for li in ol.find_all('li', recursive=False):

                backlink_span = li.find('span', class_='mw-cite-backlink')
                if backlink_span:
                    backlink_span.decompose()

                text = " ".join(li.stripped_strings)

                if text.startswith('^ '):
                    text = text[2:].strip()
                text = re.sub(r'^(\^\s*([a-z]\s+)*)+', '', text).strip()

                refs[current_ref_number] = text
                current_ref_number += 1

        return refs
    
    def extract_introduction(self, full_url):
        soup = self.extract_page_soup(full_url)
        if not soup:
            return ""

        content = soup.select_one('div.mw-parser-output')
        if not content:
            print("Article body container not found.")
            return ""

        paras = []
        node = content.find('p')
        if not node:
            print("No paragraphs found in intro.")
            return ""

        while node:
            if node.name == 'h2':
                break
            if node.name == 'p':
                text = " ".join(node.stripped_strings)
                if text:
                    paras.append(text)
            node = node.find_next_sibling()

        return "\n\n".join(paras)

    def reference_fusion(self, intro_text, references):
        fused = intro_text.strip() + "\n\nReferences:\n"
        count = 0
        for i in range(1, len(references) + 1):
            pattern = f" [ {i} ] "
            if pattern in intro_text:
                fused += f"[{i}] {references[i]}\n"
                count += 1
        if count == 0:
            return intro_text  # no references were cited
        return fused.strip()


if __name__ == "__main__":
    parser = WikipediaParser()

    url = "https://en.wikipedia.org/wiki/Recurrent_neural_network"
    # print("\nINTRODUCTION:\n" + "-"*20)
    # intro = parser.extract_introduction(url)
    # print(intro + "...\n")  # just show first 500 chars
    # print("-" * 20)
    # references = parser.extract_references(target_url)
    # print("-" * 20)

    # for r in references:
    #     print(f"[{r}] {references[r][:100]}...")
    intro = parser.extract_introduction(url)
    refs = parser.extract_references(url)
    fused = parser.reference_fusion(intro, refs)
    print(fused)
