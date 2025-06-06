from paper_processor import PaperProcessor

# Initialize processor
processor = PaperProcessor(2)

# Start with a root keyword
root_keyword = "Recurrent Neural Network"

# Process the keyword and all its sub-keywords
processor.process_keyword(root_keyword)

# Print database statistics
print("\n== Database Statistics ==")
print(f"Total keywords processed: {len(processor.processed_keywords)}")
print("\nKeywords and their papers:")
for keyword in processor.database.get_all_keywords():
    papers = processor.database.get_keyword_papers(keyword)
    print(f"\n-- {keyword} --")
    print(f"Number of papers: {len(papers)}")
    for paper in papers:
        print(f"  - {paper.get('title', 'No title')}")

# print("\nRemaining keywords to process:")
remaining = processor.database.get_remaining_keywords()
# if remaining:
#     for keyword in remaining:
#         print(f"  - {keyword}")
# else:
#     print("  None")


#Build system to extract claims
#then pick claims that are relevant
# then look for citations in those claims and if not we have to look for related citations else where in the text.