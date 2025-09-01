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

1. Identify any claims in the text relating to the foundational academic papers that are associated with the primary development/invention of {keyword}. Be picky, but extract all claims that provide direct information on foundational papers. If a claim is found, simply select the sentence/sentences (word for word). If you don't find any simply use the placeholder XXX.
2. List any other important technical or conceptual keywords found in the text that are related to the topic and may be worth tracking in a research database. These should be tangible concepts. Be picky with this as well.

Return your answer in this format:

- Sentence/Sentences deemed important (extract directly from the content. When possible try to expand claims such that they contain a reference. Don't add any extra text, put extracted text in quotes.) – *Explanation of why it was chosen* - <Paper in the claim (from references if available) - ["<Name of the paper if identifiable by reference else name as mentioned in the claim>"] :-: <Author(s)> (<Year>)>. If any information is unavailable in the claim use XXX as a placeholder. if there are multiple papers in one claim make them separate entries. Ensure to check the references first.

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
        
    
    def extract_papers_and_keywords_general(self, section_title, all_text, explicit_references, keyword):
        prompt = f"""
You are aiding in building a database of keywords and the foundational research papers that **originated or invented them**. 
Given the following article titled "{section_title}", do the following:

1. Identify only those claims that explicitly discuss the **first or foundational papers** responsible for the creation, invention, or primary development of {keyword}. 
   - Do NOT include papers that are merely related, derivative, or follow-up work.
   - If a claim is found, extract the sentence/sentences **word for word**. 
   - If no truly foundational claim is present, use XXX.
   - Be EXTREMELY picky; this is the single most important criterion.

2. Inline citations may exist in the form of [1], (Author, Year), or doi: links. Always cross-check and resolve them against the provided references list when possible.

3. The article may contain irrelevant content (navigation menus, copyright statements, site promotions, tags, URLs). **Ignore all of this** and focus only on meaningful content describing the origin of {keyword}.

Return your answer in this format:

- Sentence/Sentences deemed important (extract directly from the content. Include references if possible. Do not add extra text, put text in quotes.) – *Explanation of why it is foundational* - <Paper in the claim (from references if available - ["<Name of the paper if identifiable by reference else name as mentioned in the claim>"]) :-: <Author(s)> (<Year>)>. 
- If multiple papers appear in one claim, separate them as distinct entries. Always cross-check references first.

Article Content:
\"\"\"
{all_text}
\"\"\"

References:
\"\"\"
{explicit_references}
\"\"\"
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API call failed: {e}")
            return None