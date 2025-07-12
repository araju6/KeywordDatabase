import json
import os
from typing import Dict, List, Optional

class KeywordDatabase:
    def __init__(self, db_file: str = "keyword_database.json"):
        """
        Initialize the keyword database.
        
        Args:
            db_file: Path to the JSON database file
        """
        self.db_file = db_file
        self.data = self._load_database()
        
    def _load_database(self) -> Dict:
        """Load the database from JSON file or create new if doesn't exist."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    # We no longer rely on 'claim_chains', but we need to ensure 
                    # the basic structure exists if loading an old file.
                    if "keywords" not in data:
                        data["keywords"] = {}
                    if "remaining_to_process" not in data:
                        data["remaining_to_process"] = []
                    
                    # If 'claim_chains' exists in the loaded data, we ignore it for new operations
                    # as per the user's request, but keep the structure clean for saving.
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
        # Removed "claim_chains" from the structure
        return {
            "keywords": {},  # keyword -> list of papers
            "remaining_to_process": [],  # list of keywords to process
        }
    
    def _save_database(self):
        """Save the current database state to JSON file."""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    # Modified add_paper to accept parent_keyword and child_claim parameters
    def add_paper(self, keyword: str, paper: Dict, gemini_claim: str = None, parent_keyword: Optional[str] = None, child_claim: Optional[str] = None, child_keyword=None) -> None:
        """
        Add a paper to a keyword's entry.
        
        Args:
            keyword: The keyword to add the paper to
            paper: The paper information dictionary
            gemini_claim: The claim text extracted by Gemini that led to this paper
            parent_keyword: The parent keyword that led to this one (if applicable)
            child_claim: The uncited claim from the parent that led to this keyword (if applicable)
        """
        if keyword not in self.data["keywords"]:
            self.data["keywords"][keyword] = []
            
        # Check if paper already exists (based on title and URL for robustness)
        paper_title = paper.get("title", "")
        paper_url = paper.get("url", "")
        
        if not paper_title or not paper_url:  # Skip if no title or URL
            return
            
        # Check if this exact paper (by title and URL) is already in the list for this keyword
        # Note: We should ideally also check if the *child_claim* is different, 
        # but for simplicity, we assume one entry per paper per keyword for now.
        if any(p.get("url") == paper_url for p in self.data["keywords"][keyword]):
             print(f"Paper '{paper_title}' already exists for keyword '{keyword}', skipping add.")
             return

        # Ensure all required fields are present and add new fields
        paper_data = {
            "title": paper_title,
            "url": paper_url,
            "abstract": paper.get("abstract", ""),
            "citations": paper.get("citations", 0),
            "reasoning": paper.get("reasoning", gemini_claim), # Use 'reasoning' from paper_info if available, or the gemini_claim
            
            # New fields: Store parent_keyword and the linking child_claim
            # We explicitly set child_claim to None if it's not provided, ensuring it's only populated for papers found via recursion
            "parent_keyword": parent_keyword, 
            "child_claim": child_claim,
            "child_keyword": child_keyword
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
    
    # Removed the following methods as requested:
    # def add_claim_to_chain(self, ...): 
    # def get_claim_chain(self, ...): 
    # def get_all_linked_keywords(self, ...):