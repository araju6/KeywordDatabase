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
            
            Based solely on this information, rate this paper's relevance to the query on a scale from 0 to 9 (inclusive),
            where 1 means completely irrelevant and 9 means perfectly relevant. If a paper is lacking certain information, assess it using what is provided and what you know about the paper.
            Remember that for certain topics it may be unlikely that a single paper
            can be attributed with the credit, so in such cases adjust your scores higher accordingly. Grade VERY harshly. Only give high scores to papers that you think are truly relevant.
            
            Return only a number between 0 and 9 (inclusive). Give a 0 for papers with any missing fields.
            """
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="gpt-4o",
                temperature=0,
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(score_text[0])
            score = max(1, min(9, score))
            scores.append(score)
            feedback.append(score_text[4:])
        return scores, feedback
    

if __name__ == "__main__":
    p = Paper_Verifier()
    papers = {"abstract" : "We describe a new learning procedure, back-propagation, for networks of neurone-like units. The procedure repeatedly adjusts the weights of the connections in the network so as to minimize a measure of the difference between the actual output vector of the net and the desired output vector. As a result of the weight adjustments, internal ‘hidden’ units which are not part of the input or output come to represent important features of the task domain, and the regularities in the task are captured by the interactions of these units. The ability to create useful new features distinguishes back-propagation from earlier, simpler methods such as the perceptron-convergence procedure1.", "link": "https://doi.org/10.1038/323533a0", 
              "citations": 26382, "title": "Learning representations by back-propagating errors", "reasoning":"This paper is fundamental to the resurgence of neural networks in the 1980s and introduced the backpropagation algorithm, crucial for training RNNs (though not specifically about RNN architecture itself)"}
    query = "Which foundational research papers were responsible for inventing/discovering Recurrent Neural Networks in Computer Science?"
    print(p.verify_papers([papers], query))