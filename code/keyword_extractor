# keyword_term_extractor.py

from typing import Optional
# Assuming GeminiKeywordPaperExtractor is available and provides a 'model' attribute
# from gemini import GeminiKeywordPaperExtractor 

class KeywordTermExtractor:
    def __init__(self, gemini_extractor):
        """
        Initializes the KeywordTermExtractor with a GeminiKeywordPaperExtractor instance.
        """
        self.gemini_extractor = gemini_extractor

    def extract_key_term(self, section: str, claim: str) -> Optional[str]:
        """
        Extracts a single key technical term from a given claim using the Gemini model.
        
        Args:
            section: The section title (can be empty if not applicable).
            claim: The claim text from which to extract the key term.
            
        Returns:
            The extracted key term (normalized) or None if no suitable term is found.
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
            response = self.gemini_extractor.model.generate_content(prompt)
            result = response.text
            
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