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
                    # Ensure claim_chains exists in existing databases
                    if "claim_chains" not in data:
                        data["claim_chains"] = {}
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
            "claim_chains": {}  # keyword -> list of claims in the chain that led to this keyword
        }
    
    def _save_database(self):
        """Save the current database state to JSON file."""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_paper(self, keyword: str, paper: Dict, parent_claim: str = None) -> None:
        """
        Add a paper to a keyword's entry.
        
        Args:
            keyword: The keyword to add the paper to
            paper: The paper information dictionary
            parent_claim: The claim from the parent keyword that led to this paper, if any
        """
        if keyword not in self.data["keywords"]:
            self.data["keywords"][keyword] = []
            
        # Check if paper already exists (based on title)
        paper_title = paper.get("title", "")
        if not paper_title:  # Skip if no title
            return
            
        # Check if this paper is already in the database
        if not any(p.get("title") == paper_title for p in self.data["keywords"][keyword]):
            # Ensure all required fields are present
            paper_data = {
                "title": paper_title,
                "url": paper.get("url", ""),
                "abstract": paper.get("abstract", ""),
                "citations": paper.get("citations", 0),
                "reasoning": paper.get("reasoning", ""),
                "child_claim": parent_claim  # Add parent claim information
            }
            self.data["keywords"][keyword].append(paper_data)
            print(f"Added paper '{paper_title}' to keyword '{keyword}'")
            self._save_database()
    
    def add_to_process(self, keyword: str) -> None:
        """
        Add a keyword to the list of remaining keywords to process.
        
        Args:
            keyword: The keyword to add
        """
        if keyword not in self.data["remaining_to_process"]:
            self.data["remaining_to_process"].append(keyword)
            self._save_database()
    
    def get_keyword_papers(self, keyword: str) -> List[Dict]:
        """
        Get all papers for a specific keyword.
        
        Args:
            keyword: The keyword to get papers for
            
        Returns:
            List of paper dictionaries
        """
        return self.data["keywords"].get(keyword, [])
    
    def get_all_keywords(self) -> List[str]:
        """
        Get all keywords that have papers.
        
        Returns:
            List of keywords
        """
        return list(self.data["keywords"].keys())
    
    def get_remaining_keywords(self) -> List[str]:
        """
        Get all keywords that still need to be processed.
        
        Returns:
            List of keywords to process
        """
        return self.data["remaining_to_process"]
    
    def remove_from_remaining(self, keyword: str) -> None:
        """
        Remove a keyword from the remaining to process list.
        
        Args:
            keyword: The keyword to remove
        """
        if keyword in self.data["remaining_to_process"]:
            self.data["remaining_to_process"].remove(keyword)
            self._save_database()
    
    def add_claim_to_chain(self, child_keyword: str, claim_text: str, parent_keyword: str) -> None:
        """
        Add a claim to the chain of claims that led from a parent_keyword to a child_keyword.
        
        Args:
            child_keyword: The keyword that was discovered.
            claim_text: The specific text/claim from the parent's source that led to child_keyword.
            parent_keyword: The parent keyword that led to this claim.
        """
        if child_keyword not in self.data["claim_chains"]:
            self.data["claim_chains"][child_keyword] = []
            
        claim_entry = {
            "claim": claim_text,
            "parent_keyword": parent_keyword
        }
        
        # Avoid adding duplicate claim entries for the same child-parent link
        if claim_entry not in self.data["claim_chains"][child_keyword]:
            self.data["claim_chains"][child_keyword].append(claim_entry)
            self._save_database()
    
    def get_claim_chain(self, child_keyword: str, parent_keyword: Optional[str] = None) -> Optional[str]:
        """
        Retrieves the specific claim text that linked the parent_keyword to the child_keyword.
        
        Args:
            child_keyword: The keyword (child) whose claims to look up.
            parent_keyword: The specific parent keyword to filter by. If provided, returns the claim
                            that specifically links this parent to the child. If None, it attempts to
                            find any claim leading to the child (though for your current `PaperProcessor`
                            use case, `parent_keyword` will always be provided here).
            
        Returns:
            The specific claim text from the parent's source that led to the child_keyword,
            or None if no such claim is found.
        """
        if child_keyword in self.data["claim_chains"]:
            # If a specific parent is provided, find the claim from that parent
            if parent_keyword:
                for entry in self.data["claim_chains"][child_keyword]:
                    if entry['parent_keyword'] == parent_keyword:
                        return entry['claim']
            # If parent_keyword is None, you might have different behavior,
            # but for the PaperProcessor's use, parent_keyword is always provided here.
        return None

    def get_all_linked_keywords(self) -> set:
        """
        Returns a set of all child keywords that have claim chains (i.e., are linked from a parent).
        """
        return set(self.data["claim_chains"].keys())