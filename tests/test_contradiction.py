"""
test_contradiction.py - Automated unit tests for AI Contradiction Detector modules.
"""

import os
import json
import pytest
from src.pdf_reader import PDFReader, load_document
from src.cleaner import TextCleaner
from src.claims import ClaimExtractor, Claim, DocumentClaims
from src.matcher import ClaimMatcher, ClaimPair
from src.comparator import ContradictionComparator


def test_pdf_reader_raw_text():
    text = "Hello world! This is a test document."
    res = load_document(text, "test.txt")
    assert res["success"] is True
    assert res["filename"] == "test.txt"
    assert "Hello world!" in res["full_text"]


def test_cleaner():
    raw = "--- Page 1 ---\nThis is  a test sentence.  \n\n\nSecond paragraph."
    cleaned = TextCleaner.clean_text(raw)
    assert "--- Page 1 ---" not in cleaned
    assert "This is a test sentence." in cleaned
    sentences = TextCleaner.extract_sentences(cleaned)
    assert len(sentences) >= 2


def test_claim_extraction_heuristic():
    sample_text = "The company agrees to pay $50,000 USD within 30 days of contract execution. All services must be completed by December 2024."
    doc_claims = ClaimExtractor.extract_with_heuristic(sample_text, "Contract_A")
    assert doc_claims.total_claims > 0
    categories = [c.category for c in doc_claims.claims]
    assert "Financial" in categories or "Timeline" in categories or "General" in categories


def test_claim_matching():
    c1 = Claim(id="C-1", text="Payment term is 30 days.", category="Financial", key_entities=["30 days"])
    c2 = Claim(id="C-2", text="Payment term is 15 days.", category="Financial", key_entities=["15 days"])
    doc_a = DocumentClaims(doc_name="DocA", claims=[c1], total_claims=1)
    doc_b = DocumentClaims(doc_name="DocB", claims=[c2], total_claims=1)

    pairs = ClaimMatcher.match_claims(doc_a, doc_b)
    assert len(pairs) == 1
    assert pairs[0].claim_a.id == "C-1"
    assert pairs[0].claim_b.id == "C-2"


def test_contradiction_comparator_high_severity():
    c1 = Claim(id="C-1", text="Payment term is 30 days.", category="Financial")
    c2 = Claim(id="C-2", text="Payment term is 15 days.", category="Financial")
    pair = ClaimPair(id="PAIR-1", claim_a=c1, claim_b=c2, similarity=0.8, topic="Financial")

    res = ContradictionComparator.analyze_pair_heuristic(pair)
    assert res.is_contradiction is True
    assert res.severity == "HIGH"
    assert "30 days" in res.explanation or "Doc A" in res.explanation


def test_benchmark_json_test_cases():
    json_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
    assert os.path.exists(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for tc in data.get("test_cases", []):
        ca = Claim(id="C-A", text=tc["doc_a_text"], category=tc["expected_category"])
        cb = Claim(id="C-B", text=tc["doc_b_text"], category=tc["expected_category"])
        pair = ClaimPair(id=tc["id"], claim_a=ca, claim_b=cb, similarity=0.8, topic=tc["expected_category"])

        res = ContradictionComparator.analyze_pair_heuristic(pair)
        assert res.severity == tc["expected_severity"] or res.is_contradiction == tc["expected_contradiction"]
