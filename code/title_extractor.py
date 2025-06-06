class TitleExtractor:
    def __init__(self):
        pass

    def extract_titles(self, identified_claims):
        """
        Extract paper titles from identified claims.
        
        Args:
            identified_claims: List of paper claims from organizer
            
        Returns:
            List of tuples (clean_title, full_paper) where clean_title is just the paper title
        """
        clean_claims = []
        
        for paper in identified_claims:
            # Extract title from the format ["Title" :-: Author (Year)]
            if '["' in paper and '"]' in paper:
                start = paper.find('["') + 2
                end = paper.find('"]')
                clean_title = paper[start:end].strip()
                clean_claims.append((clean_title, paper))
                
        return clean_claims 