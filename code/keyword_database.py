import json
import os
from typing import Dict, List, Optional

# Import the Gemini extractor to use its model
# Assuming the file is named 'gemini.py' and contains GeminiKeywordPaperExtractor
from gemini import GeminiKeywordPaperExtractor 

class KeywordDatabase:
    def __init__(self, db_file: str = "keyword_database.json", gemini_extractor: Optional[GeminiKeywordPaperExtractor] = None):
        """
        Initialize the keyword database.
        
        Args:
            db_file: Path to the JSON database file
            gemini_extractor: An instance of GeminiKeywordPaperExtractor to make API calls for reasoning.
        """
        self.db_file = db_file
        self.gemini_extractor = gemini_extractor # Store the Gemini extractor
        self.data = self._load_database()
        
    def _load_database(self) -> Dict:
        """Load the database from JSON file or create new if doesn't exist."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    # Ensure basic structure exists for loading old files
                    if "keywords" not in data:
                        data["keywords"] = {}
                    if "remaining_to_process" not in data:
                        data["remaining_to_process"] = []
                    
                    # If 'claim_chains' exists in the loaded data, we ignore it for new operations
                    # but keep the structure clean for saving.
                    if "claim_chains" in data:
                         del data["claim_chains"] 
                         
                    return data
            except json.JSONDecodeError:
                print(f"Error reading {self.db_file}, creating new database")
                return self._create_new_database()
        else:
            return self._create_new_database()
    
    def _create_new_database(self) -> Dict:
        """Create a new empty database structure."""
        return {
            "keywords": {},  # keyword -> list of papers
            "remaining_to_process": [],  # list of keywords to process
        }
    
    def _save_database(self):
        """Save the current database state to JSON file."""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _generate_reasoning(self, keyword: str, gemini_claim: str, parent_keyword: Optional[str], child_claim: Optional[str], child_keyword: Optional[str]) -> str:
        """
        Generates a natural language justification for why a paper is associated with a keyword
        using a Gemini API call, incorporating parent/child claim context.
        """
        if not self.gemini_extractor or not self.gemini_extractor.model:
            return f"Cannot generate detailed reasoning: Gemini extractor not provided or not initialized. Original claim: {gemini_claim}"

        prompt_parts = []
        if parent_keyword and child_claim and child_keyword:
            prompt_parts.append(f"The paper was found while exploring the keyword '{keyword}', which was derived from the parent keyword '{parent_keyword}' through the claim: \"{child_claim}\" which specifically led to the child keyword '{child_keyword}'.")
        elif parent_keyword and child_claim: # Case where child_keyword is implicitly the current keyword
             prompt_parts.append(f"The paper was found while exploring the keyword '{keyword}', which was derived from the parent keyword '{parent_keyword}' through the claim: \"{child_claim}\".")
        else:
            prompt_parts.append(f"The paper is associated with the keyword '{keyword}'.")

        prompt_parts.append(f"The original claim that led to the identification of this paper is: \"{gemini_claim}\".")
        
        full_prompt = (
            f"Based on the following information, create a concise natural language justification "
            f"for why a research paper is associated with a keyword. "
            f"Focus on how the paper's identification connects to the provided claims and keyword hierarchy.\n\n"
            f"{' '.join(prompt_parts)}\n\n"
            f"Generate ONLY the justification sentence, without introducing phrases like 'This paper is associated because...' or 'The justification is...'. "
            f"Start directly with the core justification. Make it flow naturally. If the reasoning involves parent/child keywords, clearly state how they connect."
        )

        try:
            response = self.gemini_extractor.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating reasoning via Gemini: {e}")
            return f"Error generating reasoning. Original claim: {gemini_claim}"

    def add_paper(self, keyword: str, paper: Dict, gemini_claim: str = None, parent_keyword: Optional[str] = None, child_claim: Optional[str] = None, child_keyword: Optional[str] = None) -> None:
        """
        Add a paper to a keyword's entry.
        
        Args:
            keyword: The keyword to add the paper to
            paper: The paper information dictionary (should contain 'title', 'url', 'abstract', 'citations', 'reasoning' from OpenAlex)
            gemini_claim: The claim text extracted by Gemini that directly led to this paper's identification.
            parent_keyword: The parent keyword that led to this one (if applicable).
            child_claim: The uncited claim from the parent that led to this keyword (if applicable).
            child_keyword: The child keyword that was extracted from the child_claim (if applicable).
        """
        if keyword not in self.data["keywords"]:
            self.data["keywords"][keyword] = []
            
        # Check if paper already exists (based on title and URL for robustness)
        paper_title = paper.get("title", "")
        paper_url = paper.get("url", "")
        
        if not paper_title or not paper_url:  # Skip if no title or URL
            print(f"Skipping paper add: Missing title or URL for paper related to '{keyword}'.")
            return
            
        # Check if this exact paper (by URL, as title might vary slightly) is already in the list for this keyword
        if any(p.get("url") == paper_url for p in self.data["keywords"][keyword]):
             print(f"Paper '{paper_title}' already exists for keyword '{keyword}', skipping add.")
             return

        # Generate the new reasoning text using Gemini
        generated_reasoning = self._generate_reasoning(
            keyword=keyword,
            gemini_claim=gemini_claim,
            parent_keyword=parent_keyword,
            child_claim=child_claim,
            child_keyword=child_keyword # Pass this to reasoning generation
        )

        # Ensure all required fields are present and add new fields
        paper_data = {
            "title": paper_title,
            "url": paper_url,
            "abstract": paper.get("abstract", ""),
            "citations": paper.get("citations", 0),
            
            # Renamed 'reasoning' from OpenAlex/Gemini to 'claim'
            "claim": gemini_claim, # Store the exact claim from Gemini that identified the paper
            
            # New field: Generated natural language reasoning
            "reasoning": generated_reasoning,
            
            # Store parent_keyword and the linking child_claim/child_keyword
            "parent_keyword": parent_keyword, 
            "child_claim": child_claim,
            "child_keyword": child_keyword # Store the child keyword that was extracted
        }
        
        self.data["keywords"][keyword].append(paper_data)
        print(f"Added paper '{paper_title}' to keyword '{keyword}'")
        self._save_database()
    
    def add_to_process(self, keyword: str) -> None:
        """
        Add a keyword to the list of remaining keywords to process.
        """
        if keyword not in self.data["remaining_to_process"]:
            self.data["remaining_to_process"].append(keyword)
            self._save_database()
    
    def get_keyword_papers(self, keyword: str) -> List[Dict]:
        """
        Get all papers for a specific keyword.
        """
        return self.data["keywords"].get(keyword, [])
    
    def get_all_keywords(self) -> List[str]:
        """
        Get all keywords that have papers.
        """
        return list(self.data["keywords"].keys())
    
    def get_remaining_keywords(self) -> List[str]:
        """
        Get all keywords that still need to be processed.
        """
        return self.data["remaining_to_process"]
    
    def remove_from_remaining(self, keyword: str) -> None:
        """
        Remove a keyword from the remaining to process list.
        """
        if keyword in self.data["remaining_to_process"]:
            self.data["remaining_to_process"].remove(keyword)
            self._save_database()