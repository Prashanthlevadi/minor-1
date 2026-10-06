"""
cleaner.py - Text preprocessing and cleaning utilities for claim extraction.
"""

import re
from typing import List, Dict, Any


class TextCleaner:
    """
    Cleans raw document text and segments it into clean logical blocks or sentences.
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Cleans raw extracted text:
        - Removes page number markers like '--- Page 1 ---'
        - Normalizes multiple spaces, tabs, and duplicate line breaks
        - Standardizes quotes and dashes
        """
        if not raw_text:
            return ""

        # Remove page headers inserted by reader
        text = re.sub(r"--- Page \d+ ---", "", raw_text)

        # Standardize smart quotes and dashes
        text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
        text = text.replace("—", "-").replace("–", "-")

        # Remove null bytes and non-printable control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

        # Normalize multiple spaces per line
        lines = []
        for line in text.splitlines():
            line_str = re.sub(r"[ \t]+", " ", line).strip()
            if line_str:
                lines.append(line_str)

        cleaned = "\n".join(lines)
        return cleaned

    @staticmethod
    def extract_sentences(cleaned_text: str) -> List[str]:
        """
        Segments text into distinct sentence / assertion units.
        """
        if not cleaned_text:
            return []

        # Split on paragraph breaks or bullet points first
        blocks = re.split(r"\n{2,}|\n(?=[•\-\*\d+\.])", cleaned_text)
        sentences = []

        for block in blocks:
            # Sentence delimiter split
            raw_sentences = re.split(r"(?<=[.!?])\s+", block)
            for s in raw_sentences:
                s_clean = s.strip()
                # Exclude trivial titles or tiny numbers
                if len(s_clean) > 8 and not re.match(r"^\d+$", s_clean):
                    sentences.append(s_clean)

        return sentences

    @staticmethod
    def prepare_for_analysis(doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cleans document full_text and extracts sentence units.
        """
        raw_text = doc_data.get("full_text", "")
        cleaned = TextCleaner.clean_text(raw_text)
        sentences = TextCleaner.extract_sentences(cleaned)

        result = dict(doc_data)
        result["cleaned_text"] = cleaned
        result["sentences"] = sentences
        result["sentence_count"] = len(sentences)
        return result
