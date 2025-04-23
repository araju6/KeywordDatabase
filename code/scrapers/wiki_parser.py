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
        
        references_heading = None
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            if heading.get_text().strip().lower() == 'references':
                references_heading = heading
                break
        
        if not references_heading:
            print("Could not find References heading.")
            return []
        refs = {}
        current_ref_number = 1
        all_containers = soup.find_all(['div', 'ol'], class_=['reflist-columns', 'reflist', 'references'])
        valid_containers = [c for c in all_containers if c.sourceline > references_heading.sourceline]
        
        if not valid_containers:
            print("No reference containers found after References heading.")
            return []
        for container in valid_containers:
            if container.name == 'ol' and 'references' in container.get('class', []):
                ol_blocks = [container]
            else:
                ol_blocks = container.select('ol.references')
            
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
        headings = content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        all_paragraphs = content.find_all('p', recursive=True)
        all_paragraphs = [p for p in all_paragraphs if p.text.strip()]
        heading_hierarchy = {}
        current_parent = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
        for h in headings:
            level = int(h.name[1])
            heading_text = h.get_text().strip()
            current_parent[level] = heading_text
            for l in range(level + 1, 7):
                current_parent[l] = None
            if level == 2:
                heading_hierarchy[h] = heading_text
            else:
                parent_level = level - 1
                while parent_level >= 2 and current_parent[parent_level] is None:
                    parent_level -= 1
                
                if parent_level >= 2:
                    heading_hierarchy[h] = f"{current_parent[parent_level]} - {heading_text}"
                else:
                    heading_hierarchy[h] = heading_text
        first_heading_idx = float('inf')
        if headings:
            for i, p in enumerate(all_paragraphs):
                if p.sourceline > headings[0].sourceline:
                    first_heading_idx = i
                    break
        
        intro_paragraphs = all_paragraphs[:first_heading_idx] if first_heading_idx < float('inf') else all_paragraphs
        if intro_paragraphs:
            sections["Introduction"] = "\n\n".join(" ".join(p.stripped_strings) for p in intro_paragraphs)
        for i, heading in enumerate(headings):
            hierarchical_heading = heading_hierarchy.get(heading, heading.get_text().strip())
            start_idx = None
            end_idx = None
            
            for j, p in enumerate(all_paragraphs):
                if p.sourceline > heading.sourceline and start_idx is None:
                    start_idx = j
                
                if i < len(headings) - 1 and p.sourceline > headings[i+1].sourceline:
                    end_idx = j
                    break
            
            if start_idx is not None and end_idx is None:
                end_idx = len(all_paragraphs)
            
            if start_idx is not None and end_idx is not None and start_idx < end_idx:
                section_paragraphs = all_paragraphs[start_idx:end_idx]
                if section_paragraphs:
                    sections[hierarchical_heading] = "\n\n".join(" ".join(p.stripped_strings) for p in section_paragraphs)
        
        return sections

    def reference_fusion(self, sections, references):
        updated_sections = {}
        ref_used = set()
        for section_title, content in sections.items():
            section_refs = {}
            
            for i in range(1, len(references) + 1):
                pattern = f"\\[ {i} \\]"
                if re.search(pattern, content):
                    section_refs[i] = references.get(i, "Reference not found")
                    ref_used.add(i)
            if section_refs:
                fused_content = content.strip() + "\n\nReferences:\n"
                for ref_num in sorted(section_refs.keys()):
                    fused_content += f"[{ref_num}] {section_refs[ref_num]}\n"
                updated_sections[section_title] = fused_content.strip()
            else:
                updated_sections[section_title] = content
        
        return updated_sections


if __name__ == "__main__":
    parser = WikipediaParser()

    url = "https://en.wikipedia.org/wiki/convolutional_neural_network"
    # print("\nINTRODUCTION:\n" + "-"*20)
    # intro = parser.extract_introduction(url)
    # print(intro + "...\n")  # just show first 500 chars
    # print("-" * 20)
    references = parser.extract_references(url)
    # print("-" * 20)

    # for r in references:
    #     print(f"[{r}] {references[r][:100]}...")
    # intro = parser.extract_introduction(url)
    # refs = parser.extract_references(url)
    # fused = parser.reference_fusion(intro, refs)
    # print(fused)
    sections = parser.extract_sections(url)
    fused = parser.reference_fusion(sections, references)
    
    # Print all sections and their content
    for header, content in fused.items():
        print(f"\n{header}\n{'-'*len(header)}")
        print(content) 

    # print(references)




# add a function to get the keywords
# an issue is finding the keywords
# assume were given a list of the keywords
# use the list as a starting point and also crawl new pages each time