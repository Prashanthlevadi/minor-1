"""
pdf_reader.py - Reliable text extraction from text-based PDFs and document files.
"""

import os
from typing import Dict, Any, List, Optional


class PDFReader:
    """
    Handles PDF extraction using PyMuPDF (fitz) with fallback text file loading.
    """

    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes, filename: str = "uploaded.pdf") -> Dict[str, Any]:
        """
        Extract text from PDF byte content.
        """
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages_text = []
            full_text_list = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text") or ""
                text_clean = text.strip()
                if text_clean:
                    pages_text.append({
                        "page_number": page_num + 1,
                        "text": text_clean,
                        "char_count": len(text_clean)
                    })
                    full_text_list.append(f"--- Page {page_num + 1} ---\n{text_clean}")

            doc.close()
            full_text = "\n\n".join(full_text_list)

            return {
                "success": True,
                "filename": filename,
                "total_pages": len(pages_text),
                "full_text": full_text,
                "pages": pages_text,
                "char_count": len(full_text),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "total_pages": 0,
                "full_text": "",
                "pages": [],
                "char_count": 0,
                "error": f"Failed to extract PDF text: {str(e)}"
            }

    @staticmethod
    def extract_text_from_file_path(file_path: str) -> Dict[str, Any]:
        """
        Extract text from a file path (PDF, TXT, MD).
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "filename": os.path.basename(file_path),
                "total_pages": 0,
                "full_text": "",
                "pages": [],
                "char_count": 0,
                "error": f"File not found: {file_path}"
            }

        filename = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            try:
                with open(file_path, "rb") as f:
                    return PDFReader.extract_text_from_pdf_bytes(f.read(), filename)
            except Exception as e:
                return {
                    "success": False,
                    "filename": filename,
                    "total_pages": 0,
                    "full_text": "",
                    "pages": [],
                    "char_count": 0,
                    "error": f"Could not open file: {str(e)}"
                }
        else:
            # Assume text/markdown/json file
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return {
                    "success": True,
                    "filename": filename,
                    "total_pages": 1,
                    "full_text": content.strip(),
                    "pages": [{"page_number": 1, "text": content.strip(), "char_count": len(content)}],
                    "char_count": len(content),
                    "error": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "filename": filename,
                    "total_pages": 0,
                    "full_text": "",
                    "pages": [],
                    "char_count": 0,
                    "error": f"Text read error: {str(e)}"
                }


def load_document(source: Any, filename: str = "document.txt") -> Dict[str, Any]:
    """
    Convenience helper to load document from bytes, path, or raw string.
    """
    if isinstance(source, bytes):
        if filename.lower().endswith(".pdf"):
            return PDFReader.extract_text_from_pdf_bytes(source, filename)
        else:
            text = source.decode("utf-8", errors="ignore").strip()
            return {
                "success": True,
                "filename": filename,
                "total_pages": 1,
                "full_text": text,
                "pages": [{"page_number": 1, "text": text, "char_count": len(text)}],
                "char_count": len(text),
                "error": None
            }
    elif isinstance(source, str):
        if os.path.exists(source):
            return PDFReader.extract_text_from_file_path(source)
        else:
            # Plain raw text
            clean_text = source.strip()
            return {
                "success": True,
                "filename": filename,
                "total_pages": 1,
                "full_text": clean_text,
                "pages": [{"page_number": 1, "text": clean_text, "char_count": len(clean_text)}],
                "char_count": len(clean_text),
                "error": None
            }
    else:
        return {
            "success": False,
            "filename": filename,
            "total_pages": 0,
            "full_text": "",
            "pages": [],
            "char_count": 0,
            "error": "Unsupported document source input"
        }
