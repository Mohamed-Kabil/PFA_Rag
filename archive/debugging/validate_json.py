import json
import sys

def validate_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("Error: JSON root should be a list.")
        sys.exit(1)

    if len(data) == 0:
        print("Error: JSON is empty.")
        sys.exit(1)

    expected_keys = {"content", "chapter", "section", "section_index"}
    malformed_entries = []
    empty_fields = []

    for i, entry in enumerate(data):
        missing_keys = expected_keys - set(entry.keys())
        if missing_keys:
            malformed_entries.append((i, missing_keys))
        else:
            # Check for empty fields
            for key in expected_keys:
                if not entry[key] and entry[key] != 0: # allow section_index = 0
                    empty_fields.append((i, key))

    if malformed_entries:
        print(f"Found {len(malformed_entries)} malformed entries missing keys:")
        for idx, missing in malformed_entries[:10]:
            print(f"  Entry {idx} missing: {missing}")
        if len(malformed_entries) > 10:
            print("  ...")

    if empty_fields:
        print(f"Found {len(empty_fields)} empty fields:")
        for idx, key in empty_fields[:10]:
            print(f"  Entry {idx} empty key: {key}")
        if len(empty_fields) > 10:
            print("  ...")

    if not malformed_entries and not empty_fields:
        print("JSON validation successful. All expected keys are present and non-empty.")

if __name__ == "__main__":
    validate_json("PFA_Rag/data/corpus_cleaned_fr.json")
