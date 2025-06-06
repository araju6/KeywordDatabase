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
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {self.db_file}, creating new database")
                return self._create_new_database()
        else:
            return self._create_new_database()
    
    def _create_new_database(self) -> Dict:
        """Create a new empty database structure."""
        return {
            "keywords": {},  # keyword -> list of papers
            "remaining_to_process": []  # list of keywords to process
        }
    
    def _save_database(self):
        """Save the current database state to JSON file."""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_paper(self, keyword: str, paper: Dict) -> None:
        """
        Add a paper to a keyword's entry.
        
        Args:
            keyword: The keyword to add the paper to
            paper: The paper information dictionary
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
                "reasoning": paper.get("reasoning", "")
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