import re
from typing import List, Dict, Optional
import json
from db_manager import JsonDatabaseManager

class ReferenceExtractor:
    def __init__(self, json_db_manager: JsonDatabaseManager, bibliography_text: str):

        self.db_manager = json_db_manager
        self.parsed_bibliography = self._parse_bibliography(bibliography_text)
        print(f"Initialized ReferenceExtractor. Parsed {len(self.parsed_bibliography)} bibliography entries.")

    def _parse_bibliography(self, bibliography_text: str) -> Dict[int, str]:

        parsed_refs = {}
        lines = bibliography_text.split('\n')
        current_ref_num = None
        current_ref_text = []

        for line in lines:

            match = re.match(r'^\s*\[(\d+)\]\s*(.*)', line)
            if match:
                if current_ref_num is not None:
                    parsed_refs[current_ref_num] = "\n".join(current_ref_text).strip()
                
                current_ref_num = int(match.group(1))
                current_ref_text = [match.group(2).strip()]
            elif current_ref_num is not None:
                current_ref_text.append(line.strip())
        
        if current_ref_num is not None:
            parsed_refs[current_ref_num] = "\n".join(current_ref_text).strip()

        return parsed_refs

    def extract_and_add_references(self, sections: List[Dict]):
        if not self.parsed_bibliography:
            print("No bibliography entries parsed. Cannot extract references.")
            return

        print("\n--- Extracting and Adding References to Database ---")
        for section in sections:
            section_title = section.get('title')
            section_text = section.get('text_content')

            if not section_title or not section_text:
                print(f"Warning: Skipping malformed section entry: {section}")
                continue

            found_ref_matches = list(re.finditer(r'\[(\d+)\]', section_text))
            sentences = re.split(r'(?<=[.!?])\s+', section_text)
            sentences = [s.strip() for s in sentences if s.strip()]

            added_count = 0
            processed_unique_references_with_context = set() 

            for match in found_ref_matches:
                ref_num_str = match.group(1)
                try:
                    ref_num = int(ref_num_str)
                    if ref_num in self.parsed_bibliography:
                        full_reference = self.parsed_bibliography[ref_num]

                        context_sentences_for_match = []
                        for sentence in sentences:
                            if f"[{ref_num_str}]" in sentence:
                                context_sentences_for_match.append(sentence)
                        
                        for context_sentence in set(context_sentences_for_match):
                            source_entry = {
                                "source_text": full_reference,
                                "context_sentence": context_sentence
                            }
                            
                            unique_key = (full_reference, context_sentence)
                            if unique_key not in processed_unique_references_with_context:
                                self.db_manager.add_source_to_section(section_title, source_entry)
                                processed_unique_references_with_context.add(unique_key)
                                added_count += 1
                    else:
                        print(f"Warning: Reference [{ref_num}] found in '{section_title}' but not in bibliography.")
                except ValueError:
                    print(f"Warning: Could not parse reference number '{ref_num_str}' in section '{section_title}'.")
            
            if added_count > 0:
                print(f"Processed section '{section_title}': Added {added_count} unique bibliography references with context.")
            else:
                print(f"Processed section '{section_title}': No new bibliography references with context found.")

