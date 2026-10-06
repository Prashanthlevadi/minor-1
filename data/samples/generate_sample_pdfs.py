import os
import pymupdf  # PyMuPDF

def text_to_pdf(txt_path: str, pdf_path: str):
    if not os.path.exists(txt_path):
        return
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842) # A4 size

    # Insert text block
    rect = pymupdf.Rect(40, 40, 555, 800)
    page.insert_textbox(rect, content, fontsize=10, fontname="helv")

    doc.save(pdf_path)
    doc.close()

    # Verify extraction immediately
    verify_doc = pymupdf.open(pdf_path)
    extracted = verify_doc[0].get_text()
    verify_doc.close()
    print(f"Generated {os.path.basename(pdf_path)} ({len(extracted.strip())} chars extracted):")
    print(extracted[:150] + "...\n")

base_dir = os.path.dirname(__file__)
text_to_pdf(os.path.join(base_dir, "sample_contract_v1.txt"), os.path.join(base_dir, "sample_contract_v1.pdf"))
text_to_pdf(os.path.join(base_dir, "sample_contract_v2.txt"), os.path.join(base_dir, "sample_contract_v2.pdf"))
text_to_pdf(os.path.join(base_dir, "sample_policy_2023.txt"), os.path.join(base_dir, "sample_policy_2023.pdf"))
text_to_pdf(os.path.join(base_dir, "sample_policy_2024.txt"), os.path.join(base_dir, "sample_policy_2024.pdf"))
