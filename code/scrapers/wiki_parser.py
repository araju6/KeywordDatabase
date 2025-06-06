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
        
        current_path = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
        heading_full_paths = {}
        
        for h in headings:
            level = int(h.name[1])
            heading_text = h.get_text().strip()
            current_path[level] = heading_text
            
            for l in range(level + 1, 7):
                current_path[l] = None
            
            if level == 2:
                heading_full_paths[h] = heading_text
            else:
                path_parts = []
                for l in range(2, level):
                    if current_path[l] is not None:
                        path_parts.append(current_path[l])
                
                path_parts.append(heading_text)
                heading_full_paths[h] = " - ".join(path_parts)
        
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
            full_path_heading = heading_full_paths.get(heading, heading.get_text().strip())
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
                    sections[full_path_heading] = "\n\n".join(" ".join(p.stripped_strings) for p in section_paragraphs)
        
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

    def extract_keywords(self, text, existing_keywords=None):
        if existing_keywords is None:
            existing_keywords = set()
        else:
            existing_keywords = set(existing_keywords)
            
        potential_keywords = set(re.findall(r'(?:[A-Z][a-z]+ ){1,3}[A-Z][a-z]+', text))
        
        technical_terms = set(re.findall(r'\b(?:[a-z]+-[a-z]+|[a-z]+)\b', text.lower()))
        
        term_counts = {}
        for term in technical_terms:
            if len(term) > 4:
                term_counts[term] = text.lower().count(term)
        
        frequent_terms = {term for term, count in term_counts.items() if count > 2}
        
        all_keywords = existing_keywords.union(potential_keywords).union(frequent_terms)
        
        return list(all_keywords)
    
    def crawl_related_pages(self, base_url, depth=1, max_pages=5, keywords=None):
        if keywords is None:
            keywords = []
            
        visited = set()
        to_visit = [(base_url, 0)]
        results = {}
        
        while to_visit and len(visited) < max_pages:
            current_url, current_depth = to_visit.pop(0)
            
            if current_url in visited or current_depth > depth:
                continue
                
            print(f"Crawling: {current_url} (depth {current_depth})")
            visited.add(current_url)
            
            sections = self.extract_sections(current_url)
            references = self.extract_references(current_url)
            fused_content = self.reference_fusion(sections, references)
            
            results[current_url] = {
                'sections': fused_content,
                'depth': current_depth
            }
            
            all_content = " ".join(sections.values())
            keywords = self.extract_keywords(all_content, keywords)
            
            if current_depth < depth:
                soup = self.extract_page_soup(current_url)
                if soup:
                    content_div = soup.select_one('div.mw-parser-output')
                    if content_div:
                        links = content_div.find_all('a', href=True)
                        for link in links:
                            href = link.get('href', '')
                            if href.startswith('/wiki/') and ':' not in href:
                                full_url = f"https://en.wikipedia.org{href}"
                                if full_url not in visited:
                                    to_visit.append((full_url, current_depth + 1))
        
        return results[:10], keywords


if __name__ == "__main__":
    parser = WikipediaParser()

    url = "https://en.wikipedia.org/wiki/Recurrent_neural_network"
    references = parser.extract_references(url)
    sections = parser.extract_sections(url)
    fused = parser.reference_fusion(sections, references)
    
    for header, content in fused.items():
        print(f"\n{header}\n{'-'*len(header)}")
        print(content)
    
    # Uncomment to use the new crawling functionality
    # results, keywords = parser.crawl_related_pages(url, depth=1, max_pages=3)
    # print("\nExtracted Keywords:")
    # for keyword in keywords[:20]:  # Show first 20 keywords
    #    print(f"- {keyword}")