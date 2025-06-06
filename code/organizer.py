class PaperOrganizer:
    def __init__(self):
        self.identified_sources = []
        self.non_identified_sources = []

    def organize_papers(self, paper_list):
        for _, papers in paper_list:
            for paper in papers.split("\n"):
                paper = paper.strip("-• ").strip()
                if not paper:
                    continue
                    
                if "XXX" in paper:
                    self.non_identified_sources.append(paper)
                else:
                    self.identified_sources.append(paper)
        
        return self.identified_sources, self.non_identified_sources 