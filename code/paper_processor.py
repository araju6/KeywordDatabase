from organizer import PaperOrganizer
from gemini import GeminiKeywordPaperExtractor
from paper_retrievers.openAlex_retriever import OpenAlexRetriever
from paper_verifier import Paper_Verifier
from keyword_database import KeywordDatabase
from scrapers.wiki_parser import WikipediaParser
from title_extractor import TitleExtractor
import time

class PaperProcessor:
    def __init__(self, max_recursion_depth: int = 0):
        """
        Initialize the PaperProcessor.
        
        Args:
            max_recursion_depth: Maximum depth for processing non-identified sources. 
                               0 means no recursion (only process initial sources).
                               1 means process non-identified sources once.
        """
        self.organizer = PaperOrganizer()
        self.title_extractor = TitleExtractor()
        self.gemini_extractor = GeminiKeywordPaperExtractor()
        self.openalex = OpenAlexRetriever()
        self.verifier = Paper_Verifier()
        self.database = KeywordDatabase()
        self.wiki_parser = WikipediaParser()
        self.timeout_seconds = 30  # Timeout for Gemini API calls
        self.max_recursion_depth = max_recursion_depth
        self.processed_keywords = set()  # Track processed keywords to avoid cycles
        self.non_identified_sources = []

    def extract_key_term(self, section: str, claim: str) -> str:
        """
        Extract a single key term from a non-identified source claim.
        
        Args:
            section: The section title
            claim: The claim text containing XXX
            
        Returns:
            The extracted key term or None if no term found
        """
        # Skip if claim is just XXX or empty
        if not claim or claim.strip() == "XXX":
            return None
            
        try:
            # Ask Gemini to extract the key term
            prompt = f"""Given this claim from the {section} section: "{claim}"
            Extract the single most important key term that should be researched to verify this claim.
            Return ONLY the term itself, with no additional text, no explanations, no formatting.
            Do not say "the term is" or "here is" or any other phrases.
            Just return the term itself.
            For example:
            Input: "The LSTM architecture was revolutionary"
            Output: LSTM
            
            Input: "The vanishing gradient problem affects training"
            Output: vanishing gradient

            If there is nothing suitable say XXX
            
            Now extract the key term from the claim above:"""
            
            # Use a direct API call to Gemini instead of the paper extractor
            result = self.gemini_extractor.model.generate_content(prompt).text
            
            if result:
                # Clean up the result to get just the term
                term = result.strip().strip('"').strip("'").strip()
                # Skip if term is just XXX
                if term == "XXX":
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

    def process_keyword(self, keyword: str, current_depth: int = None, parent_keyword: str = None, processed_chain: set = None):
        """
        Process a keyword by finding and verifying its papers.
        
        Args:
            keyword: The keyword to process
            current_depth: Current recursion depth for non-identified sources.
                          If None, uses max_recursion_depth for initial call.
            parent_keyword: The parent keyword that led to this one, if any
            processed_chain: Set of keywords in the current processing chain to prevent cycles
        """
        # Set initial depth to max_recursion_depth if not specified
        if current_depth is None:
            current_depth = self.max_recursion_depth
            
        # Initialize processed chain if not provided
        if processed_chain is None:
            processed_chain = set()
            
        # Skip if already processed or in current chain (prevents cycles)
        if keyword in self.processed_keywords or keyword in processed_chain:
            print(f"\nSkipping {keyword} - already processed or in current chain")
            return
            
        # Skip if max depth reached
        if current_depth < 0:
            print(f"\nSkipping {keyword} - max depth reached")
            return
            
        # If depth is 0, we're done before processing any papers
        if current_depth == 0:
            print("\nDepth is 0, skipping all paper processing")
            return
            
        # Add to processed sets
        self.processed_keywords.add(keyword)
        processed_chain.add(keyword)
        self.database.remove_from_remaining(keyword)  # Remove from remaining to process
        
        print(f"\n{'='*50}")
        print(f"Processing keyword: {keyword} (depth: {current_depth})")
        if parent_keyword:
            print(f"Parent keyword: {parent_keyword}")
        print(f"Current chain: {processed_chain}")
        print(f"{'='*50}")
        
        # Get Wikipedia content
        print(f"\nStep 1: Fetching Wikipedia content for {keyword}")
        wiki_url = f"https://en.wikipedia.org/wiki/{keyword.replace(' ', '_')}"
        sections = self.wiki_parser.extract_sections(wiki_url)
        references = self.wiki_parser.extract_references(wiki_url)
        sections = self.wiki_parser.reference_fusion(sections, references)
        print(f"Found {len(sections)} sections")
        
        # Get target sections
        print("\nStep 2: Extracting target sections")
        target_sections = {}
        for title, content in sections.items():
            if title.lower() == "introduction" or "history" in title.lower():
                target_sections[title] = content
        print(f"Found {len(target_sections)} target sections")
        
        # Extract papers and keywords
        print("\nStep 3: Extracting papers using Gemini")
        paper_list = []
        new_keywords = []
        
        for section_title, section_text in target_sections.items():
            print(f"\nProcessing section: {section_title}")
            result = self.gemini_extractor.extract_papers_and_keywords(section_title, section_text, keyword)
            if result:
                # Split into papers and keywords
                if "New Keywords:" in result:
                    papers, keywords = result.split("New Keywords:")
                    # Add new keywords to remaining_to_process
                    for line in keywords.strip().split("\n"):
                        if line.strip().startswith("-"):
                            new_keyword = line.strip("- ").strip()
                            if new_keyword and new_keyword not in self.processed_keywords:
                                self.database.add_to_process(new_keyword)
                                new_keywords.append(new_keyword)
                else:
                    papers = result
                
                # Process papers part
                papers = papers.replace("Foundational Papers:", "").strip()
                paper_list.append((section_title, papers))
        
        print(f"Found {len(paper_list)} paper entries")
        print(f"Found {len(new_keywords)} new keywords to process")
        
        # Process papers
        print("\nStep 4: Organizing papers into identified and non-identified sources")
        identified_sources, non_identified_sources = self.organizer.organize_papers(paper_list)
        # Remove duplicates from non_identified_sources
        non_identified_sources = list(dict.fromkeys(non_identified_sources))
        print(f"Identified sources: {len(identified_sources)}")
        print(f"Non-identified sources: {[a[0] for a in self.title_extractor.extract_titles(non_identified_sources)]} ")
        
        # Extract clean titles from identified sources
        print("\nStep 5: Extracting clean titles from identified sources")
        clean_identified_sources = self.title_extractor.extract_titles(identified_sources)
        
        # Process identified sources
        print("\nStep 6: Processing identified sources")
        for clean_title, full_paper in clean_identified_sources:
            print(f"\nProcessing paper: {clean_title}")
            
            # Search in OpenAlex
            paper_info = self.openalex.search_paper(clean_title)
            
            if paper_info:
                print("Found paper info, verifying relevance...")
                
                # Add the original claim as reasoning
                paper_info['reasoning'] = full_paper
                
                # Verify the paper for current keyword
                scores, feedback = self.verifier.verify_papers([paper_info], 
                    f"Which foundational research papers were responsible for inventing/discovering {keyword} in Computer Science?")
                
                if scores and scores[0] >= 7:  # High threshold for relevance
                    print(f"Paper verified with score {scores[0]}, adding to database")
                    # Use the clean title from OpenAlex response instead of the full paper string
                    paper_info['title'] = paper_info['title']  # This is the clean title from OpenAlex
                    self.database.add_paper(keyword, paper_info)
                    
                    # If this is a child keyword, verify the paper for the parent keyword as well
                    # But only if parent is not in the current chain (prevents verification cycles)
                    if parent_keyword and parent_keyword not in processed_chain:
                        print(f"\nVerifying paper for parent keyword: {parent_keyword}")
                        parent_scores, parent_feedback = self.verifier.verify_papers([paper_info],
                            f"Which foundational research papers were responsible for inventing/discovering {parent_keyword} in Computer Science?")
                        
                        if parent_scores and parent_scores[0] >= 7:
                            print(f"Paper verified for parent with score {parent_scores[0]}, adding to parent")
                            self.database.add_paper(parent_keyword, paper_info)
                        else:
                            print(f"Paper rejected for parent with score {parent_scores[0] if parent_scores else 'N/A'}")
                else:
                    print(f"Paper rejected with score {scores[0] if scores else 'N/A'}")
            else:
                print("No paper info found in OpenAlex")
        
        # Only process non-identified sources if depth > 0
        if current_depth > 0:
            # Process non-identified sources
            print("\nStep 7: Processing non-identified sources")
            for claim in non_identified_sources:
                print(f"\nProcessing non-identified claim: {claim[:100]}...")
                key_term = self.extract_key_term("", claim)  # No section title needed
                if key_term and key_term not in processed_chain:  # Prevent cycles in key term extraction
                    print(f"Will explore: {key_term}")
                    self.database.add_to_process(key_term)
                    # Process key term with reduced depth, passing this keyword as parent and the current chain
                    self.process_keyword(key_term, current_depth - 1, keyword, processed_chain.copy())
                else:
                    print(f"Skipping {key_term} - already in current chain") 