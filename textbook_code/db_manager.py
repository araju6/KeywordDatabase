import json
import os

class JsonDatabaseManager:

    def __init__(self, db_file_path: str):
        self.db_file_path = db_file_path
        self.data = self._load_data()
        print(f"Initialized JsonDatabaseManager with database file: {self.db_file_path}")

    def _load_data(self) -> dict:
        if os.path.exists(self.db_file_path) and os.path.getsize(self.db_file_path) > 0:
            try:
                with open(self.db_file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                print("Data loaded successfully from JSON database.")
                return loaded_data
            except json.JSONDecodeError:
                print(f"Warning: JSON file '{self.db_file_path}' is empty or malformed. Starting with empty database.")
                return {}
            except Exception as e:
                print(f"An error occurred while loading data: {e}. Starting with empty database.")
                return {}
        else:
            print("JSON database file not found or is empty. Starting with empty database.")
            return {}

    def _save_data(self):
        try:
            with open(self.db_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
            print("Data saved successfully to JSON database.")
        except Exception as e:
            print(f"Error saving data to JSON file: {e}")

    def add_section_entry(self, section_title: str, section_data: dict = None):
        if section_title not in self.data:
            self.data[section_title] = {
                "details": section_data if section_data is not None else {},
                "sources": []  # Initialize with an empty list for sources
            }
            print(f"Added new section entry: '{section_title}'")
        else:
            if section_data is not None:
                self.data[section_title]["details"].update(section_data)
                print(f"Updated details for existing section: '{section_title}'")
            else:
                print(f"Section '{section_title}' already exists. No new details provided.")
        self._save_data()

    def add_source_to_section(self, section_title: str, source: str):
        if section_title not in self.data:
            self.add_section_entry(section_title) # Create section if it doesn't exist

        if source not in self.data[section_title]["sources"]:
            self.data[section_title]["sources"].append(source)
            print(f"Added source '{source}' to section '{section_title}'")
            self._save_data()
        else:
            print(f"Source '{source}' already exists in section '{section_title}'. Skipping.")

    def get_sources_for_section(self, section_title: str) -> list:
        if section_title in self.data:
            return self.data[section_title].get("sources", [])
        else:
            print(f"Section '{section_title}' not found in database.")
            return []

    def get_section_data(self, section_title: str) -> dict:
        if section_title in self.data:
            return self.data[section_title]
        else:
            print(f"Section '{section_title}' not found in database.")
            return {}

    def get_all_sections(self) -> dict:
        return self.data

    def delete_section(self, section_title: str):
        if section_title in self.data:
            del self.data[section_title]
            self._save_data()
            print(f"Section '{section_title}' deleted successfully.")
        else:
            print(f"Section '{section_title}' not found in database. Nothing to delete.")

if __name__ == "__main__":
    db_file = "clrs_sections_db.json"
    db_manager = JsonDatabaseManager(db_file)

    # Add some section entries
    db_manager.add_section_entry("Introduction to Algorithms", {"level": 1, "start_page": 1, "end_page": 10})
    db_manager.add_section_entry("Sorting Algorithms", {"level": 2, "start_page": 50, "end_page": 100})
    db_manager.add_section_entry("Merge Sort", {"level": 3, "start_page": 60, "end_page": 70})
    db_manager.add_section_entry("Quick Sort", {"level": 3, "start_page": 71, "end_page": 85})

    # Add sources to sections
    db_manager.add_source_to_section("Merge Sort", "Section 2.3.1")
    db_manager.add_source_to_section("Merge Sort", "Figure 2.4")
    db_manager.add_source_to_section("Merge Sort", "Algorithm 2.2")
    db_manager.add_source_to_section("Merge Sort", "Section 2.3.1") # This is a duplicate, will be skipped

    db_manager.add_source_to_section("Quick Sort", "Chapter 7")
    db_manager.add_source_to_section("Quick Sort", "Problem 7-2")

    db_manager.add_source_to_section("Introduction to Algorithms", "Preface")

    # Retrieve and print sources for a section
    print("\n--- Sources for Merge Sort ---")
    merge_sort_sources = db_manager.get_sources_for_section("Merge Sort")
    for source in merge_sort_sources:
        print(f"- {source}")

    print("\n--- Sources for Non-existent Section ---")
    non_existent_sources = db_manager.get_sources_for_section("Non-existent Section")
    print(f"Sources: {non_existent_sources}")

    # Get full data for a section
    print("\n--- Full Data for Quick Sort ---")
    quick_sort_data = db_manager.get_section_data("Quick Sort")
    print(json.dumps(quick_sort_data, indent=2))

    # Get all sections
    print("\n--- All Sections in DB ---")
    all_sections_data = db_manager.get_all_sections()
    print(json.dumps(all_sections_data, indent=2))

    # Delete a section
    db_manager.delete_section("Sorting Algorithms")
    print("\n--- All Sections after deletion ---")
    print(json.dumps(db_manager.get_all_sections(), indent=2))

    # Clean up the test file
    # if os.path.exists(db_file):
    #     os.remove(db_file)
    #     print(f"\nCleaned up test database file: {db_file}")
