from organizer import PaperOrganizer
from gemini import GeminiKeywordPaperExtractor
from paper_retrievers.openAlex_retriever import OpenAlexRetriever
from paper_verifier import Paper_Verifier
from keyword_database import KeywordDatabase
from scrapers.wiki_parser import WikipediaParser
from scrapers.google_search import GoogleSearcher
from title_extractor import TitleExtractor
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
        self.gemini_extractor = GeminiKeywordPaperExtractor()
        self.openalex = OpenAlexRetriever()
        self.verifier = Paper_Verifier()
        self.database = KeywordDatabase()
        self.wiki_parser = WikipediaParser()
        self.GoogleSearcher = GoogleSearcher()
        self.max_recursion_depth = max_recursion_depth
        
        # Track processed keywords globally (normalized to lowercase) to avoid cycles
        self.processed_keywords = set()  

    def extract_key_term(self, section: str, claim: str) -> Optional[str]:
        """
        Extract a single key term from a non-identified source claim using Gemini.
        """
        # Skip if claim is just XXX or empty
        if not claim or claim.strip() == "XXX":
            return None
            
        try:
            # Ask Gemini to extract the key term
            prompt = f"""Given this claim from the {section} section: "{claim}"
            Extract the single most important technical term or concept that should be researched to verify this claim.
            
            Rules:
            1. The term MUST be a technical concept, algorithm, model, or research area in computer science/ML
            2. DO NOT return common English words or non-technical terms
            3. The term should be specific enough to be researchable
            4. If the term is part of a paper title, extract the technical concept instead
            5. Return ONLY the term itself, with no additional text
            6. If no suitable technical term exists, return XXX
            7. DO NOT return authors or years only paper concepts.
            8. The term can be multiple words if it's a complete technical concept
            
            Examples:
            Input: "The LSTM architecture was revolutionary"
            Output: LSTM
            
            Input: "The vanishing gradient problem affects training"
            Output: vanishing gradient
            
            Input: "Bidirectional recurrent neural networks were developed to process sequences in both directions"
            Output: Bidirectional recurrent neural networks
            
            Now extract the key term from the claim above:"""
            
            # Use a direct API call to Gemini
            result = self.gemini_extractor.model.generate_content(prompt).text
            
            if result:
                # Clean up the result to get just the term
                term = result.strip().strip('"').strip("'").strip()
                # Skip if term is just XXX or a common word
                if term == "XXX" or term.lower() in {'the', 'and', 'or', 'but', 'only', 'just', 'very', 'much', 'many', 'few', 'some', 'all', 'none'}:
                    return None
                # Remove any formatting or extra text
                if ":" in term:
                    term = term.split(":")[-1].strip()
                if "-" in term:
                    term = term.split("-")[-1].strip()
                if "•" in term:
                    term = term.split("•")[-1].strip()
                return term
        except Exception as e:
            print(f"Error extracting key term: {e}")
        return None

    def process_keyword(self, keyword: str, current_depth: int = None, parent_keyword: Optional[str] = None, processed_chain: Optional[Set[str]] = None, claim_from_parent_to_this_keyword: Optional[str] = None):
        """
        Process a keyword by finding and verifying its papers.
        """
        # --- Normalize keywords to lowercase for consistent processing and cycle detection ---
        normalized_keyword = keyword.lower()
        
        # Set initial depth if not specified
        if current_depth is None:
            current_depth = self.max_recursion_depth
            
        # Initialize processed chain if not provided
        if processed_chain is None:
            processed_chain = set()
            
        # Handle cycles and depth limits using the normalized keyword
        if normalized_keyword in self.processed_keywords or normalized_keyword in processed_chain:
            print(f"\nSkipping {keyword} - already processed or in current chain")
            return
            
        if current_depth < 0:
            print(f"\nSkipping {keyword} - max depth reached")
            return
            
        if current_depth == 0:
            print("\nDepth is 0, skipping all paper processing")
            return
            
        # Add the normalized keyword to processed sets
        self.processed_keywords.add(normalized_keyword)
        
        # Create a copy of the processed_chain for this recursion level
        current_chain_copy = processed_chain.copy()
        current_chain_copy.add(normalized_keyword)
        
        self.database.remove_from_remaining(normalized_keyword) 
        
        print(f"\n{'='*50}")
        print(f"Processing keyword: {normalized_keyword} (depth: {current_depth})")
        if parent_keyword:
            print(f"Parent keyword: {parent_keyword.lower()}")
        print(f"Current chain: {current_chain_copy}")
        print(f"{'='*50}")
        
        # --- Step 1: Fetching Wikipedia content ---
        print(f"\nStep 1: Fetching Wikipedia content for {keyword}")
        # Note: We use the original keyword for search to ensure we find the correct page, 
        # but process the results using the normalized keyword.
        wiki_url = self.GoogleSearcher.find_wikipedia_page(keyword) 
        if not wiki_url:
            print(f"Could not find Wikipedia page for {keyword}, skipping...")
            return
        
        render_url = f"{wiki_url}?action=render"
        
        sections = self.wiki_parser.extract_sections(render_url)
        references = self.wiki_parser.extract_references(render_url)
        sections = self.wiki_parser.reference_fusion(sections, references)
        print(f"Found {len(sections)} sections")
        
        # --- Step 2: Get target sections ---
        print("\nStep 2: Extracting target sections")
        target_sections = {}
        for title, content in sections.items():
            if title.lower() == "introduction" or "history" in title.lower():
                target_sections[title] = content
        print(f"Found {len(target_sections)} target sections")
        
        # --- Step 3: Extract papers and keywords using Gemini ---
        print("\nStep 3: Extracting papers using Gemini")
        paper_list = []
        new_keywords = []
        
        for section_title, section_text in target_sections.items():
            print(f"\nProcessing section: {section_title}")
            result = self.gemini_extractor.extract_papers_and_keywords(section_title, section_text, keyword)
            if result:
                # Assuming Gemini output separation by "New Keywords:"
                if "New Keywords:" in result:
                    papers, keywords = result.split("New Keywords:")
                    # Add new keywords to remaining_to_process
                    for line in keywords.strip().split("\n"):
                        if line.strip().startswith("-"):
                            new_keyword = line.strip("- ").strip()
                            # Normalize the new keyword before tracking
                            normalized_new_keyword = new_keyword.lower()
                            if normalized_new_keyword and normalized_new_keyword != "None" and normalized_new_keyword not in self.processed_keywords:
                                self.database.add_to_process(normalized_new_keyword)
                                new_keywords.append(normalized_new_keyword)
                else:
                    papers = result
                
                # Process papers part
                papers = papers.replace("Foundational Papers:", "").strip()
                paper_list.append((section_title, papers))
        
        print(f"Found {len(paper_list)} paper entries")
        print(f"Found {len(new_keywords)} new keywords to process")
        
        # --- Step 4: Organizing papers into identified and non-identified sources ---
        print("\nStep 4: Organizing papers into identified and non-identified sources")
        
        # FIX: Reset PaperOrganizer's internal lists to prevent accumulation from previous runs
        self.organizer.identified_sources = []
        self.organizer.non_identified_sources = []
        
        identified_sources, non_identified_sources_raw = self.organizer.organize_papers(paper_list)
        non_identified_sources = non_identified_sources_raw
        
        print(f"Identified sources: {len(identified_sources)}")
        print(f"Non-identified sources: {non_identified_sources}")
        
        # --- Step 5: Extract clean titles from identified sources ---
        print("\nStep 5: Extracting clean titles from identified sources")
        clean_identified_sources = self.title_extractor.extract_titles(identified_sources)
        
        # --- Step 6: Processing identified sources ---
        print("\nStep 6: Processing identified sources")
        for clean_title_from_gemini, gemini_full_claim_text in clean_identified_sources:
            print(f"\nProcessing paper: {clean_title_from_gemini}")

            # Search in OpenAlex 
            paper_info = self.openalex.search_paper(clean_title_from_gemini)

            if paper_info:
                print("Found paper info, verifying relevance...")

                # Verify for current keyword
                scores, feedback = self.verifier.verify_papers([paper_info],
                    f"Which foundational research papers were responsible for inventing/discovering {keyword} in Computer Science?")

                if scores and scores[0] >= 7:  
                    print(f"Paper verified with score {scores[0]}, adding to database for {normalized_keyword}")
                    
                    # Determine child_claim and parent_keyword for the current paper entry
                    current_child_claim = claim_from_parent_to_this_keyword
                    
                    # We only set child_keyword if this is a recursive call (parent_keyword exists)
                    current_child_keyword = normalized_keyword if parent_keyword else None

                    # Add the paper to the database for the current keyword (child or initial)
                    self.database.add_paper(
                        normalized_keyword, # Use normalized keyword
                        paper_info, 
                        gemini_full_claim_text, 
                        parent_keyword=parent_keyword.lower() if parent_keyword else None, # Use normalized parent keyword
                        child_claim=current_child_claim,
                        child_keyword=current_child_keyword 
                    )

                    # If this is a child keyword, verify the paper for the parent keyword as well
                    if parent_keyword:
                        print(f"\nVerifying paper for parent keyword: {parent_keyword}")

                        original_claim_from_parent = claim_from_parent_to_this_keyword
                        parent_paper_info = paper_info.copy()
                        
                        # Add reasoning for parent context
                        parent_paper_info['reasoning'] = f"Found via child keyword '{normalized_keyword}'. Derived from parent's claim: \"{original_claim_from_parent}\"."

                        parent_scores, parent_feedback = self.verifier.verify_papers([parent_paper_info],
                            f"Which foundational research papers were responsible for inventing/discovering {parent_keyword} in Computer Science?")
                        
                        if parent_scores and parent_scores[0] >= 7:
                            print(f"Paper verified for parent with score {parent_scores[0]}, adding to parent")
                            
                            # Add the paper to the parent keyword's entry.
                            self.database.add_paper(
                                parent_keyword.lower(), # Normalize parent keyword
                                paper_info, 
                                gemini_full_claim_text, 
                                parent_keyword=None, 
                                child_claim=original_claim_from_parent,
                                child_keyword=normalized_keyword # Add the child keyword here
                            )
                        else:
                            print(f"Paper rejected for parent with score {parent_scores[0] if parent_scores else 'N/A'}")
                else:
                    print(f"Paper rejected with score {scores[0] if scores else 'N/A'}")
            else:
                print("No paper info found in OpenAlex")
        
        # --- Step 7: Process non-identified sources (Recursion) ---
        if current_depth > 0:
            print("\nStep 7: Processing non-identified sources")
            for claim in non_identified_sources:
                print(f"\nProcessing non-identified claim: {claim[:100]}...")
                
                # Extract key term
                key_term = self.extract_key_term("", claim)
                
                # Normalize extracted key term before recursion check
                normalized_key_term = key_term.lower() if key_term else None
                
                # Recursion check: Check against the current chain copy to prevent cycles
                if normalized_key_term and normalized_key_term not in current_chain_copy:
                    print(f"Will explore: {key_term}")
                    self.database.add_to_process(normalized_key_term)
                    
                    # Recursively process the new normalized keyword
                    self.process_keyword(
                        normalized_key_term, 
                        current_depth - 1, 
                        normalized_keyword, 
                        current_chain_copy, 
                        claim
                    )
                else:
                    print(f"Skipping {key_term} - already in current chain or no valid term extracted")