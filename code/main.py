from scrapers.wiki_parser import WikipediaParser
from gemini import GeminiKeywordPaperExtractor

keyword = "Recurrent Neural Network"
wiki_url = "https://en.wikipedia.org/wiki/Recurrent_neural_network"

wiki_parser = WikipediaParser()
sections = wiki_parser.extract_sections(wiki_url)
references = wiki_parser.extract_references(wiki_url)
sections = wiki_parser.reference_fusion(sections, references)

target_sections = {}
for title, content in sections.items():
    if title.lower() == "introduction" or "history" in title.lower():
        target_sections[title] = content

gemini_extractor = GeminiKeywordPaperExtractor()
paper_list = []
keyword_set = set()

for section_title, section_text in target_sections.items():
    result = gemini_extractor.extract_papers_and_keywords(section_title, section_text, keyword)

    papers, keywords = result.split("New Keywords:")
    papers = papers.replace("Foundational Papers:", "").strip()
    keywords = keywords.strip().split("\n")

    paper_list.append((section_title, papers))
    for kw in keywords:
        kw = kw.strip("-• ").strip()
        if kw:
            keyword_set.add(kw)


# print("== All Foundational Papers ==")
# out = []
# for section, papers in paper_list:
#     # print(f"\n-- {section} --\n{papers}")
#     print(papers)
#     print(type(papers))

#     # out += papers

all_papers = []

print("== All Foundational Papers ==")
for section, papers in paper_list:
    # print(papers)  # You can remove this if you don’t want to print
    # Split by lines to extract individual paper titles
    for line in papers.split("\n"):
        line = line.strip("-• ").strip()
        if line != "XXX":
            all_papers.append(line)

print(all_papers)
# print("\n== All Unique New Keywords ==")
# for kw in sorted(keyword_set):
#     print(f"- {kw}")
# print(papers)


#test the model accuracy and precision
# after that build  a grader to grade each citqation accuracy
    # make a report document
