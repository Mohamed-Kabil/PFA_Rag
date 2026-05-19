"""
Run chunking evaluation on the existing corpus sample and save chunking_eval.json.
Usage: python -m backend.run_eval
"""
import json
from pathlib import Path

from backend.chunking import ChunkingManager

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INPUT = DATA_DIR / "corpus_cleaned_fr.json"
OUTPUT = DATA_DIR / "chunking_eval.json"


def main():
    print(f"Loading corpus from {INPUT} ...")
    manager = ChunkingManager(str(INPUT))

    sample_content = []
    for entry in manager.data[:50]:
        if entry.get("content") and len(entry["content"]) > 100:
            sample_content.append(entry["content"])
            if len(sample_content) >= 10:
                break

    if not sample_content:
        print("No sample content found.")
        return

    sample_text = "\n\n".join(sample_content)
    best_method, scores = manager.evaluate_methods(sample_text)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"best_method": best_method, "scores": scores}, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {OUTPUT}")
    print(f"Best method: {best_method}")


if __name__ == "__main__":
    main()
