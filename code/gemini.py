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

1. Identify the foundational academic papers that are associated with the primary development/invention of {keyword}. Only list old and foundational papers that INVENTED the concept. Be EXTREMELY picky and only select papers if they were very very direcly influential. Ensure you only cite papers that are in the citations. If you don't find any simply use the placeholder XXX.
2. List any other important technical or conceptual keywords found in the text that are related to the topic and may be worth tracking in a research database. These should be tangible concepts be quite picky with this as well.

Return your answer in this format:

Foundational Papers:
- <Paper title or topic> by <Author(s)> (<Year>) – <Explanation of why it was chosen>

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

