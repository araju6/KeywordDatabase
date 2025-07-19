import os
import json # For pretty printing the final database state

# Import the classes from their respective files
# Ensure these files (pdf_ingester_class.py, json_db_manager_class.py, reference_extractor_class.py)
# are in the same directory as this script.
from pdf_parser import PdfIngester
from db_manager import JsonDatabaseManager
from citation_connecter import ReferenceExtractor

def main():
    clrs_pdf_path = "files/algos_tb.pdf"
    json_db_file = "clrs_textbook_map.json"

    if os.path.exists(json_db_file):
        os.remove(json_db_file)
        print(f"Cleaned up existing database file: {json_db_file}")

    print("\n--- Initializing PDF Ingester ---")
    pdf_ingester = PdfIngester(clrs_pdf_path)

    if not pdf_ingester.document:
        print("Failed to load PDF. Exiting.")
        return

    print("\n--- Extracting Bibliography ---")
    bibliography_text = pdf_ingester.extract_bibliography()
    if not bibliography_text:
        print("Warning: Could not extract bibliography. Reference extraction might be incomplete.")
    else:
        print(f"Bibliography extracted (snippet): {bibliography_text[:200]}...")

    print("\n--- Initializing JSON Database Manager ---")
    db_manager = JsonDatabaseManager(json_db_file)

    print("\n--- Extracting All Sections from PDF ---")
    all_sections_from_pdf = pdf_ingester.extract_all_sections()
    print(f"Total sections extracted from PDF: {len(all_sections_from_pdf)}")

    print("\n--- Populating Database with Section Details ---")
    for section_data in all_sections_from_pdf:
        section_details = {
            "level": section_data['level'],
            "start_page": section_data['start_page'],
            "end_page": section_data['end_page'],
            "text_content_snippet": section_data['text_content'][:500] + "..." if len(section_data['text_content']) > 500 else section_data['text_content']
        }
        db_manager.add_section_entry(section_data['title'], section_details)
    print("All sections added to database (details only).")

    print("\n--- Initializing Reference Extractor ---")
    ref_extractor = ReferenceExtractor(db_manager, bibliography_text)



    print("\n--- Extracting and Adding References to Database ---")
    ref_extractor.extract_and_add_references(all_sections_from_pdf)
    print("Reference extraction complete.")

    # --- Step 7: Finalize and display results ---
    print("\n--- Processing Complete ---")
    print(f"Final database saved to: {json_db_file}")

    print("\n--- Contents of the JSON Database ---")
    final_db_content = db_manager.get_all_sections()
    print(json.dumps(final_db_content, indent=2))

    # --- Step 8: Close PDF document ---
    pdf_ingester.close_pdf()
    print("\nPDF document closed.")

if __name__ == "__main__":
    main()
