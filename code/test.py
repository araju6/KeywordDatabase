from gemini import GeminiKeywordPaperExtractor
from scrapers.general_scraper import WebPageExtractor

url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC9377665/"
extractor = WebPageExtractor(url)
data = extractor.run()

gemini_extractor = GeminiKeywordPaperExtractor()
print(gemini_extractor.extract_papers_and_keywords_general(data["metadata"]['title'], data["all_text"], data["explicit_references"], "CRISPR"))