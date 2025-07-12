import openai
from openai import OpenAI
import os
from dotenv import load_dotenv


class Paper_Verifier:
    def __init__(self):
        self.OPEN_API_KEY = api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.OPEN_API_KEY)
        
    def verify_papers(self, papers, query):
        scores = []
        feedback = []
        
        for paper in papers:
            abstract = paper.get('abstract', 'No abstract available')
            link = paper.get('link', 'No link available')
            citations = paper.get('citations', 0)
            title = paper.get('title', 'No title Available')
            reasoning = paper.get('reasoning', 'No Reasoning Available')
            
            prompt = f"""
            You are evaluating the relevance of a research paper to a given query.
            
            Query: "{query}"
            
            Paper Information:
            Abstract: {abstract}
            Link: {link}
            Number of Citations: {citations}
            Title: {title}
            Reasoning: {reasoning}
            
            Based on this information, rate this paper's relevance to the query on a scale from 0 to 9 (inclusive):
            
            * **0-3:** Not relevant or barely relevant.
            * **4-6:** Moderately relevant, but not foundational.
            * **7-9:** Highly relevant and foundational to the topic.
            
            Assess the paper's relevance based on the available information. If a paper is lacking certain information (like abstract or link), rely on the title, citations, and reasoning provided. 
            
            Remember that for certain topics, it may be unlikely that a single paper is solely responsible for the invention; score based on its foundational contribution.
            
            Return ONLY a single integer score between 0 and 9. Do not include any other text.
            """
            
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="gpt-4o-mini",
                temperature=0, # Use temperature 0 for consistent scoring
            )
            
            # Extract the score from the response, handling potential formatting issues
            response_text = response.choices[0].message.content.strip()
            
            # We expect a single digit. Attempt to parse it as an integer.
            try:
                # Use regular expression to find the first number in the response
                import re
                match = re.search(r'\d+', response_text)
                if match:
                    score = int(match.group(0))
                else:
                    score = 0 # Default to 0 if no number found

            except ValueError:
                print(f"Warning: Could not parse score from response: '{response_text}'. Defaulting to 0.")
                score = 0
            
            # Clamp the score between 0 and 9 (inclusive, based on the prompt)
            score = max(0, min(9, score))
            scores.append(score)
            
            # We instructed the model to return ONLY the integer, so there is no feedback text to append.
            # If you want feedback, you would need to modify the prompt and parsing logic.
            feedback.append("") # Keeping the feedback list structure for consistency
            
        return scores, feedback

if __name__ == "__main__":
    # Test case remains the same
    p = Paper_Verifier()
    papers = [{"abstract" : "We describe a new learning procedure, back-propagation, for networks of neurone-like units. The procedure repeatedly adjusts the weights of the connections in the network so as to minimize a measure of the difference between the actual output vector of the net and the desired output vector. As a result of the weight adjustments, internal ‘hidden’ units which are not part of the input or output come to represent important features of the task domain, and the regularities in the task are captured by the interactions of these units. The ability to create useful new features distinguishes back-propagation from earlier, simpler methods such as the perceptron-convergence procedure1.", 
               "link": "https://doi.org/10.1038/323533a0", 
               "citations": 26382, 
               "title": "Learning representations by back-propagating errors", 
               "reasoning":"This paper is fundamental to the resurgence of neural networks in the 1980s and introduced the backpropagation algorithm, crucial for training RNNs (though not specifically about RNN architecture itself)"
               }]
    
    query = "Which foundational research papers were responsible for inventing/discovering Recurrent Neural Networks in Computer Science?"
    print(p.verify_papers(papers, query))