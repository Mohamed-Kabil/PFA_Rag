import fitz
doc = fitz.open(r"C:\Users\moham\Desktop\PFA\documents\project_form.pdf")
print(f"Total pages: {len(doc)}")
for i in range(min(12, len(doc))):
    print(f"\n=== PAGE {i+1} ===")
    print(doc[i].get_text())
