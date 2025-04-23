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
    
    def extract_sections(self, full_url):
        soup = self.extract_page_soup(full_url)
        if not soup:
            return {}

        content = soup.select_one('div.mw-parser-output')
        if not content:
            print("Article body container not found.")
            return {}

        sections = {}
        intro_content = []
        current_element = content.find('p')
        while current_element and current_element.name == 'p':
            text = " ".join(current_element.stripped_strings)
            if text:
                intro_content.append(text)
            current_element = current_element.find_next_sibling()
        
        if intro_content:
            sections["Introduction"] = "\n\n".join(intro_content)
        headings = content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for i, heading in enumerate(headings):
            heading_text = heading.get_text().strip()
            section_content = []
            element = heading.find_next()
            while element:
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                    
                if element.name == 'p':
                    text = " ".join(element.stripped_strings)
                    if text:
                        section_content.append(text)
                element = element.find_next()
                if i < len(headings) - 1 and element == headings[i + 1]:
                    break
            if section_content:
                sections[heading_text] = "\n\n".join(section_content)
        
        return sections

    def reference_fusion(self, intro_text, references):
        fused = intro_text.strip() + "\n\nReferences:\n"
        count = 0
        for i in range(1, len(references) + 1):
            pattern = f" [ {i} ] "
            if pattern in intro_text:
                fused += f"[{i}] {references[i]}\n"
                count += 1
        if count == 0:
            return intro_text
        return fused.strip()


if __name__ == "__main__":
    parser = WikipediaParser()

    url = "https://en.wikipedia.org/wiki/CRISPR"
    # print("\nINTRODUCTION:\n" + "-"*20)
    # intro = parser.extract_introduction(url)
    # print(intro + "...\n")  # just show first 500 chars
    # print("-" * 20)
    # references = parser.extract_references(target_url)
    # print("-" * 20)

    # for r in references:
    #     print(f"[{r}] {references[r][:100]}...")
    # intro = parser.extract_introduction(url)
    # refs = parser.extract_references(url)
    # fused = parser.reference_fusion(intro, refs)
    # print(fused)
    sections = parser.extract_sections(url)
    
    # Print all sections and their content
    for header, content in sections.items():
        print(f"\n{header}\n{'-'*len(header)}")
        print(f"{content}...") 




# add a function to get the keywords
# an issue is finding the keywords
# assume were given a list of the keywords
# use the list as a starting point and also crawl new pages each time