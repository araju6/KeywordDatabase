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
            Claim and Reasoning: {reasoning}
            
            Based on this information, rate this paper's relevance to the query on a scale from 0 to 9 (inclusive):
            
            * **0-3:** Not relevant or barely relevant.
            * **4-6:** Moderately relevant, but not foundational.
            * **7-9:** Highly relevant and foundational to the topic.
            
            Assess the paper's relevance based on the available information. If a paper is lacking certain information (like abstract or link), rely on the title, citations, and reasoning provided. 
            
            Remember that for certain topics, it may be unlikely that a single paper is solely responsible for the invention; score based on its foundational contribution. Be EXTREMELY strict. Only papers that are directly related to the founding of the concept should be scored well.
            
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
    papers = [{"abstract" : "A neural network model for a mechanism of visual pattern recognition is proposed in this paper. The network is self-organized by “learning without a teacher”, and acquires an ability to recognize stimulus patterns based on the geometrical similarity (Gestalt) of their shapes without affected by their positions. This network is given a nickname “neocognitron”. After completion of self-organization, the network has a structure similar to the hierarchy model of the visual nervous system proposed by Hubel and Wiesel. The network consits of an input layer (photoreceptor array) followed by a cascade connection of a number of modular structures, each of which is composed of two layers of cells connected in a cascade. The first layer of each module consists of “S-cells”, which show characteristics similar to simple cells or lower order hypercomplex cells, and the second layer consists of “C-cells” similar to complex cells or higher order hypercomplex cells. The afferent synapses to each S-cell have plasticity and are modifiable. The network has an ability of unsupervised learning: We do not need any “teacher” during the process of self-organization, and it is only needed to present a set of stimulus patterns repeatedly to the input layer of the network. The network has been simulated on a digital computer. After repetitive presentation of a set of stimulus patterns, each stimulus pattern has become to elicit an output only from one of the C-cell of the last layer, and conversely, this C-cell has become selectively responsive only to that stimulus pattern. That is, none of the C-cells of the last layer responds to more than one stimulus pattern. The response of the C-cells of the last layer is not affected by the pattern's position at all. Neither is it affected by a small change in shape nor in size of the stimulus pattern", 
               "link": "None", 
               "citations": 3290, 
               "title": "Handwritten Digit Recognition with a Back-Propagation Network", 
               "reasoning":"LeCun, Y.; Boser, B.; Denker, J. S.; Henderson, D.; Howard, R. E.; Hubbard, W.; Jackel, L. D. (December 1989). Backpropagation Applied to Handwritten Zip Code Recognition . Neural Computation . 1 (4): 541– 551. – *This sentence references a pivotal paper demonstrating the application of backpropagation in CNNs for handwritten digit recognition."
               }]
    
    query = "Which foundational research papers were responsible for inventing/discovering Convolutional Neural Networks in Computer Science?"
    print(p.verify_papers(papers, query))