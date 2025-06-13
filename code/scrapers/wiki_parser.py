import requests
from bs4 import BeautifulSoup
import re

class WikipediaParser:
    API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
    def __init__(self, user_agent=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'WikipediaParser/1.0'
        })

    def _call_api(self, params):
        resp = self.session.get(self.API_ENDPOINT, params={**params, 'format': 'json'})
        resp.raise_for_status()
        return resp.json()

    def extract_sections(self, page_title):
        """Fetch sections via MediaWiki API and return dict of heading -> plain-text body with hierarchy."""
        sections = {}

        # Fetch the lead (introduction) section
        try:
            lead_data = self._call_api({
                'action': 'parse',
                'page': page_title,
                'prop': 'text',
                'section': 0
            })
            html = lead_data['parse']['text']['*']
            soup = BeautifulSoup(html, 'html.parser')
            paras = [
                p.get_text(' ', strip=True)
                for p in soup.find_all('p')
                if p.get_text(strip=True)
            ]
            sections["Introduction"] = "\n\n".join(paras)
        except Exception as e:
            print(f"Failed to fetch intro section: {e}")

        # Get list of all sections and build a map from number -> title for hierarchy
        data = self._call_api({
            'action': 'parse',
            'page': page_title,
            'prop': 'sections'
        })

        section_titles_by_number = {}
        for sec in data['parse'].get('sections', []):
            sec_number = sec.get('number', '')
            title = sec.get('line', '')
            section_titles_by_number[sec_number] = title

        for sec in data['parse'].get('sections', []):
            idx = sec['index']
            sec_number = sec.get('number', '')
            title = sec.get('line', '')

            # Build hierarchical title
            if '.' in sec_number:
                parts = sec_number.split('.')
                # Remove the last part (this section)
                parent_number = '.'.join(parts[:-1])
                parent_title = section_titles_by_number.get(parent_number, '')
                if parent_title:
                    full_title = f"{parent_title} – {title}"
                else:
                    full_title = title
            else:
                full_title = title

            try:
                sec_data = self._call_api({
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text',
                    'section': idx
                })
                html = sec_data['parse']['text']['*']
                soup = BeautifulSoup(html, 'html.parser')
                paras = [
                    p.get_text(' ', strip=True)
                    for p in soup.find_all('p')
                    if p.get_text(strip=True)
                ]
                sections[full_title] = "\n\n".join(paras)
            except Exception as e:
                print(f"Failed to fetch section {title}: {e}")

        return sections



    def extract_page_soup(self, full_url):
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



if __name__ == '__main__':
    parser = WikipediaParser()
    page_title = 'diffusion_model'
    url = f'https://en.wikipedia.org/wiki/{page_title}'

    # Extract body sections via API
    sections = parser.extract_sections(page_title)
    # Extract references via HTML scraping
    references = parser.extract_references(url)
    # Fuse references into sections
    fused = parser.reference_fusion(sections, references)

    for title, content in fused.items():
        print(f"\n=== {title} ===\n{content}...\n")
    # for header, content in fused.items():
    #     print(f"\n{header}\n{'-'*len(header)}")
    #     print(content)
    
    # Uncomment to use the new crawling functionality
    # results, keywords = parser.crawl_related_pages(url, depth=1, max_pages=3)
    # print("\nExtracted Keywords:")
    # for keyword in keywords[:20]:  # Show first 20 keywords
    #    print(f"- {keyword}")