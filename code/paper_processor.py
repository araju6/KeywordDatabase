from organizer import PaperOrganizer
from gemini import GeminiKeywordPaperExtractor
from paper_retrievers.openAlex_retriever import OpenAlexRetriever
from paper_verifier import Paper_Verifier
from keyword_database import KeywordDatabase
from scrapers.wiki_parser import WikipediaParser
from scrapers.google_search import GoogleSearcher
from title_extractor import TitleExtractor
from keyword_extractor import KeywordTermExtractor

import time
import re

import os
import time
import re
from typing import List, Dict, Optional, Set, Tuple
import os
import time
import re
from typing import List, Dict, Optional, Set, Tuple

class PaperProcessor:
    def __init__(self, max_recursion_depth: int = 0):
        """
        Initialize the PaperProcessor.
        """
        self.organizer = PaperOrganizer()
        self.title_extractor = TitleExtractor()
        self.gemini_extractor = GeminiKeywordPaperExtractor() # Keep this as it's used by KeywordTermExtractor and for other Gemini calls
        self.openalex = OpenAlexRetriever()
        self.verifier = Paper_Verifier()
        self.database = KeywordDatabase()
        self.wiki_parser = WikipediaParser()
        self.GoogleSearcher = GoogleSearcher()
        
        self.gemini_extractor = GeminiKeywordPaperExtractor() # This instance is now passed to KeywordDatabase
        self.openalex = OpenAlexRetriever()
        self.verifier = Paper_Verifier()
        
        # Pass the gemini_extractor to KeywordDatabase
        self.database = KeywordDatabase(gemini_extractor=self.gemini_extractor)
        
        self.wiki_parser = WikipediaParser()
        self.GoogleSearcher = GoogleSearcher()
        
        self.keyword_term_extractor = KeywordTermExtractor(self.gemini_extractor)
        
        self.max_recursion_depth = max_recursion_depth
        self.processed_keywords = set()

    # REMOVED: The extract_key_term method is no longer directly in PaperProcessor

    def process_keyword(self, keyword: str, current_depth: int = None, parent_keyword: Optional[str] = None, processed_chain: Optional[Set[str]] = None, claim_from_parent_to_this_keyword: Optional[str] = None):
        """
        Orchestrates the process of finding and verifying papers for a keyword.
        """
        # --- Normalize and Setup ---
        normalized_keyword = keyword.lower()
        
        if current_depth is None:
            current_depth = self.max_recursion_depth
            
        if processed_chain is None:
            processed_chain = set()
            
        # Handle cycles and depth limits
        if normalized_keyword in self.processed_keywords or normalized_keyword in processed_chain:
            print(f"\nSkipping {keyword} - already processed or in current chain")
            return
            
        if current_depth < 0:
            print(f"\nSkipping {keyword} - max depth reached")
            return
            
        if current_depth == 0:
            print("\nDepth is 0, skipping all paper processing")
            return
            
        self.processed_keywords.add(normalized_keyword)
        
        current_chain_copy = processed_chain.copy()
        current_chain_copy.add(normalized_keyword)
        
        self.database.remove_from_remaining(normalized_keyword) 
        
        print(f"\n{'='*50}")
        print(f"Processing keyword: {normalized_keyword} (depth: {current_depth})")
        if parent_keyword:
            print(f"Parent keyword: {parent_keyword.lower()}")
        print(f"Current chain: {current_chain_copy}")
        print(f"{'='*50}")
        
        # --- Step 1 & 2: Fetching and Parsing Wikipedia Content ---
        print(f"\nStep 1: Fetching Wikipedia content for {keyword}")
        wiki_url = self.GoogleSearcher.find_wikipedia_page(keyword) 
        if not wiki_url:
            print(f"Could not find Wikipedia page for {keyword}, skipping...")
            return
        
        render_url = f"{wiki_url}?action=render"
        
        sections = self.wiki_parser.extract_sections(render_url)
        references = self.wiki_parser.extract_references(render_url)
        sections = self.wiki_parser.reference_fusion(sections, references)
        print(f"Found {len(sections)} sections")
        
        target_sections = self._get_target_sections(sections)
        
        # --- Step 3: Extract Papers and Keywords using Gemini ---
        paper_list, new_keywords = self._extract_papers_and_keywords(target_sections, keyword)
        
        # Add new keywords to the database queue for processing later
        for kw in new_keywords:
            self.database.add_to_process(kw) 
        
        # --- Step 4: Organizing Papers ---
        print("\nStep 4: Organizing papers into identified and non-identified sources")
        self.organizer.reset() # Ensure organizer is clean for this run
        identified_sources, non_identified_sources = self.organizer.organize_papers(paper_list)
        
        print(f"Identified sources: {identified_sources}")
        print(f"Non-identified sources: {non_identified_sources}")
        
        # --- Step 5: Extract clean titles ---
        clean_identified_sources = self.title_extractor.extract_titles(identified_sources)
        
        # --- Step 6: Processing Identified Sources (OpenAlex and Verification) ---
        self._process_identified_sources(
            clean_identified_sources, 
            normalized_keyword, 
            parent_keyword, 
            claim_from_parent_to_this_keyword
        )
        
        # --- Step 7: Process Non-identified Sources (Recursion) ---
        if current_depth > 0:
            self._process_non_identified_sources(
                non_identified_sources, 
                current_depth, 
                normalized_keyword, 
                current_chain_copy
            )

    # --- Helper methods (Refactored logic) ---

    def _get_target_sections(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Extracts 'Introduction' and 'History' sections."""
        print("\nStep 2: Extracting target sections")
        target_sections = {}
        for title, content in sections.items():
            if title.lower() == "introduction" or "history" in title.lower():
                target_sections[title] = content
        print(f"Found {len(target_sections)} target sections")
        return target_sections

    def _extract_papers_and_keywords(self, target_sections: Dict[str, str], keyword: str) -> Tuple[List[Tuple[str, str]], List[str]]:
        """Extracts papers and new keywords from target sections using Gemini."""
        print("\nStep 3: Extracting papers using Gemini")
        paper_list = []
        new_keywords = []

        for section_title, section_text in target_sections.items():
            print(f"\nProcessing section: {section_title}")
            result = self.gemini_extractor.extract_papers_and_keywords(section_title, section_text, keyword)
            
            if result:
                if "New Keywords:" in result:
                    papers, keywords = result.split("New Keywords:")
                    for line in keywords.strip().split("\n"):
                        if line.strip().startswith("-"):
                            new_keyword = line.strip("- ").strip()
                            normalized_new_keyword = new_keyword.lower()
                            if normalized_new_keyword and normalized_new_keyword != "none" and normalized_new_keyword not in self.processed_keywords:
                                new_keywords.append(normalized_new_keyword)
                else:
                    papers = result
                
                papers = papers.replace("Foundational Papers:", "").strip()
                paper_list.append((section_title, papers))

        print(f"Found {len(paper_list)} paper entries")
        print(f"Found {len(new_keywords)} new keywords to process")
        return paper_list, new_keywords

    def _process_identified_sources(self, clean_identified_sources: List[Tuple[str, str]], normalized_keyword: str, parent_keyword: Optional[str], claim_from_parent_to_this_keyword: Optional[str]):
        """Processes identified sources by searching OpenAlex, verifying, and adding to database."""
        print("\nStep 6: Processing identified sources")
        for clean_title_from_gemini, gemini_full_claim_text in clean_identified_sources:
            print(f"\nProcessing paper: {clean_title_from_gemini}")

            paper_info = self.openalex.search_paper(clean_title_from_gemini)
            paper_info['reasoning'] = gemini_full_claim_text
            if paper_info:
                print("Found paper info, verifying relevance...")

                # Verify for current keyword
                scores, _ = self.verifier.verify_papers([paper_info],
                    f"Which foundational research papers were responsible for inventing/discovering {normalized_keyword} in Computer Science?")

                print(gemini_full_claim_text)
                if scores and scores[0] >= 6:  
                    print(f"Paper verified with score {scores[0]}, adding to database for {normalized_keyword}")
                    
                    current_child_keyword_for_db = normalized_keyword if parent_keyword else None

                    self.database.add_paper(
                        normalized_keyword, 
                        paper_info, 
                        gemini_full_claim_text, 
                        parent_keyword=parent_keyword.lower() if parent_keyword else None, 
                        child_claim=claim_from_parent_to_this_keyword,
                        child_keyword=current_child_keyword_for_db 
                    )

                    # If this is a child keyword, verify and add for the parent keyword
                    if parent_keyword:
                        self._verify_and_add_to_parent(
                            paper_info, 
                            gemini_full_claim_text, 
                            normalized_keyword, 
                            parent_keyword, 
                            claim_from_parent_to_this_keyword
                        )
                else:
                    print(f"Paper rejected with score {scores[0] if scores else 'N/A'}")
            else:
                print("No paper info found in OpenAlex")

    def _verify_and_add_to_parent(self, paper_info: Dict, gemini_full_claim_text: str, normalized_child_keyword: str, parent_keyword: str, original_claim_from_parent: str):
        """Verifies a paper for the parent keyword and adds it to the database."""
        print(f"\nVerifying paper for parent keyword: {parent_keyword}")
        
        parent_paper_info = paper_info.copy()
        parent_paper_info['reasoning'] = f"Found via child keyword '{normalized_child_keyword}'. Derived from parent's claim: \"{original_claim_from_parent}\"."

        parent_scores, _ = self.verifier.verify_papers([parent_paper_info],
            f"Which foundational research papers were responsible for inventing/discovering {parent_keyword} in Computer Science?")
        print(_)
        if parent_scores and parent_scores[0] >= 6:
            print(f"Paper verified for parent with score {parent_scores[0]}, adding to parent")
            
            self.database.add_paper(
                parent_keyword.lower(), 
                paper_info, 
                gemini_full_claim_text, 
                parent_keyword=None, 
                child_claim=original_claim_from_parent,
                child_keyword=normalized_child_keyword 
            )
        else:
            print(f"Paper rejected for parent with score {parent_scores[0] if parent_scores else 'N/A'}")

    def _process_non_identified_sources(self, non_identified_sources: List[str], current_depth: int, normalized_keyword: str, current_chain_copy: Set[str]):
        """Processes non-identified sources and initiates recursion for new keywords."""
        print("\nStep 7: Processing non-identified sources")
        
        for claim in non_identified_sources:
            print(f"\nProcessing non-identified claim: {claim[:100]}...")
            
            # Call the extract_key_term method from the new KeywordTermExtractor instance
            key_term = self.keyword_term_extractor.extract_key_term("", claim)
            
            normalized_key_term = key_term.lower() if key_term else None
            
            if normalized_key_term and normalized_key_term not in current_chain_copy:
                print(f"Will explore: {key_term}")
                self.database.add_to_process(normalized_key_term)
                
                self.process_keyword(
                    normalized_key_term, 
                    current_depth - 1, 
                    normalized_keyword, 
                    current_chain_copy, 
                    claim
                )
            else:
                print(f"Skipping {key_term} - already in current chain or no valid term extracted")
