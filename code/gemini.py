import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiKeywordPaperExtractor:
    def __init__(self, model_name="gemini-2.0-flash"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def extract_papers_and_keywords(self, section_title, section_content, keyword):
        prompt = f"""
You are aiding in building a database of keywords and the foundational research papers that invented them. 
Given the following Wikipedia section titled "{section_title}", do the following:

1. Identify any claims in the text relating to the foundational academic papers that are associated with the primary development/invention of {keyword}. Be extremely picky and only select claims if they are direcly providing information on the foundational papers. If a claim is found, simply select the sentence/sentences (word for word). If you don't find any simply use the placeholder XXX.
2. List any other important technical or conceptual keywords found in the text that are related to the topic and may be worth tracking in a research database. These should be tangible concepts be quite picky with this as well.

Return your answer in this format:

Foundational Claims:
- Sentence/Sentences deemed important (extract directly from the content. When possible try to expand claims such that they contain a reference) – *Explanation of why it was chosen* - <list of papers in claim - ["Name of the paper if identifiable by reference else name as mentioned in the claim" :-: <Author(s)> (<Year>)]>. If any information is unavailable in the claim use XXX as a placeholder.

New Keywords:
- <keyword1>
- <keyword2>
...

Section Content:
\"\"\"
{section_content}
\"\"\"
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API call failed: {e}")
            return None

