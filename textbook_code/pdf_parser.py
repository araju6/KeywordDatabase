import fitz
import re

class PdfIngester:

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.document = None
        self.table_of_contents = []
        self._load_pdf()

    def _load_pdf(self):
        try:
            self.document = fitz.open(self.pdf_path)
            self.table_of_contents = self.document.get_toc()
            print(f"Successfully loaded PDF: {self.pdf_path}")
            print(f"Extracted {len(self.table_of_contents)} TOC entries.")
        except fitz.FileNotFoundError:
            print(f"Error: PDF file not found at {self.pdf_path}")
            self.document = None
        except Exception as e:
            print(f"An error occurred while loading the PDF: {e}")
            self.document = None

    def get_table_of_contents(self) -> list:
        if not self.document:
            print("PDF document not loaded. Cannot retrieve TOC.")
            return []
        return self.table_of_contents

    def _get_page_range_for_section(self, toc_index: int) -> tuple[int, int]:
        if not self.document or not (0 <= toc_index < len(self.table_of_contents)):
            return -1, -1

        current_level, current_title, start_page = self.table_of_contents[toc_index]
        end_page = self.document.page_count


        for i in range(toc_index + 1, len(self.table_of_contents)):
            next_level, _, next_page = self.table_of_contents[i]
            if next_level <= current_level:
                end_page = next_page
                break
        
        return start_page - 1, end_page - 1

    def extract_all_sections(self) -> list[dict]:
        if not self.document:
            print("PDF document not loaded. Cannot extract sections.")
            return []
        if not self.table_of_contents:
            print("No Table of Contents found. Cannot extract sections by title.")
            return []

        all_sections_data = []

        for i, (level, title, _) in enumerate(self.table_of_contents):
            start_page_idx, end_page_idx = self._get_page_range_for_section(i)
            
            section_text = []
            for page_num in range(start_page_idx, end_page_idx):
                if 0 <= page_num < self.document.page_count: # Ensure page number is valid
                    page = self.document.load_page(page_num)
                    section_text.append(page.get_text())
                else:
                    print(f"Warning: Attempted to access invalid page {page_num} for section '{title}'. Skipping.")
                    break # Stop if an invalid page is encountered within a section

            all_sections_data.append({
                "title": title,
                "level": level,
                "start_page": start_page_idx + 1, # Store as 1-based for user clarity
                "end_page": end_page_idx + 1,     # Store as 1-based for user clarity
                "text_content": "\n".join(section_text).strip()
            })
            print(f"Extracted section: '{title}' (Pages {start_page_idx + 1}-{end_page_idx + 1})")

        return all_sections_data

    def extract_bibliography(self) -> str:

        if not self.document:
            print("PDF document not loaded. Cannot extract bibliography.")
            return ""

        bibliography_text = []
        bibliography_start_page = -1

        for i, (level, title, page_num) in enumerate(self.table_of_contents):
            if re.search(r'bibliograph|reference', title, re.IGNORECASE):
                bibliography_start_page = page_num - 1
                _, end_page_idx = self._get_page_range_for_section(i)
                
                print(f"Found bibliography/references in TOC: '{title}' starting on page {page_num}")
                for p_num in range(bibliography_start_page, end_page_idx):
                    if 0 <= p_num < self.document.page_count:
                        page = self.document.load_page(p_num)
                        bibliography_text.append(page.get_text())
                return "\n".join(bibliography_text).strip()

        print("Bibliography not found in TOC. Scanning last pages...")
        scan_pages = min(20, self.document.page_count)
        for p_num in range(self.document.page_count - scan_pages, self.document.page_count):
            if p_num >= 0: # Ensure we don't go below page 0
                page = self.document.load_page(p_num)
                text = page.get_text()

                if re.search(r'^\s*(bibliography|references)\s*$', text.split('\n')[0], re.IGNORECASE | re.MULTILINE):
                    bibliography_start_page = p_num
                    print(f"Found bibliography/references by scanning at page {p_num + 1}")

                    for final_p_num in range(bibliography_start_page, self.document.page_count):
                        page = self.document.load_page(final_p_num)
                        bibliography_text.append(page.get_text())
                    return "\n".join(bibliography_text).strip()

        print("Bibliography/References section not found.")
        return ""

    def close_pdf(self):

        if self.document:
            self.document.close()
            self.document = None
            print("PDF document closed.")

if __name__ == "__main__":
    clrs_pdf_path = "files/algos_tb.pdf" 

    ingester = PdfIngester(clrs_pdf_path)

    if ingester.document:

        print("\n--- Table of Contents ---")
        toc = ingester.get_table_of_contents()
        for entry in toc:
            print(f"  Level {entry[0]}: {entry[1]} (Page {entry[2]})")

        print("\n--- Extracting All Sections ---")
        all_sections = ingester.extract_all_sections()
        print(f"\nTotal sections extracted: {len(all_sections)}")
        if all_sections:
            print("\nFirst 3 extracted sections:")
            for i, section in enumerate(all_sections[:3]):
                print(f"  Title: {section['title']}")
                print(f"  Level: {section['level']}")
                print(f"  Pages: {section['start_page']} - {section['end_page']}")
                print(f"  Content snippet: {section['text_content']}...")
                print("-" * 30)
        print("\n--- Extracting Bibliography ---")
        bibliography_content = ingester.extract_bibliography()
        if bibliography_content:
            print(f"Bibliography content snippet: {bibliography_content[:500]}...")
        else:
            print("Bibliography not found or extracted.")

    ingester.close_pdf()
