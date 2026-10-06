"""
matcher.py - Align matching claims between two documents based on semantic similarity.
"""

import re
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from src.claims import Claim, DocumentClaims


class ClaimPair(BaseModel):
    id: str
    claim_a: Claim
    claim_b: Claim
    similarity: float = Field(description="Semantic similarity score between 0.0 and 1.0")
    topic: str = Field(default="General", description="Shared topic or category")


class ClaimMatcher:
    """
    Matches relevant claim pairs across Document A and Document B.
    """

    @staticmethod
    def _tokenize(text: str) -> set:
        """
        Tokenize and clean words for text matching.
        """
        text_clean = re.sub(r"[^\w\s]", " ", text.lower())
        words = set(text_clean.split())
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "to", "from", "in", "out",
            "on", "off", "over", "under", "again", "further", "then", "once",
            "and", "or", "but", "if", "because", "as", "until", "while", "of",
            "at", "by", "for", "with", "about", "against", "between", "into",
            "through", "during", "before", "after", "above", "below", "this",
            "that", "these", "those", "shall", "will", "must", "can", "should"
        }
        return words - stopwords

    @classmethod
    def calculate_similarity(cls, text1: str, text2: str, entities1: List[str] = None, entities2: List[str] = None) -> float:
        """
        Calculates hybrid similarity based on word overlap and entity intersection.
        """
        words1 = cls._tokenize(text1)
        words2 = cls._tokenize(text2)

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Entity bonus if same key entities (numbers, dates, proper nouns) match
        entity_bonus = 0.0
        if entities1 and entities2:
            e1_set = set(e.lower() for e in entities1)
            e2_set = set(e.lower() for e in entities2)
            shared_entities = e1_set.intersection(e2_set)
            if shared_entities:
                entity_bonus = min(0.35, 0.15 * len(shared_entities))

        total_sim = min(1.0, jaccard * 0.7 + entity_bonus + (0.15 if any(w in text2.lower() for w in words1) else 0.0))
        return round(total_sim, 3)

    @classmethod
    def match_claims(
        cls,
        doc_a_claims: DocumentClaims,
        doc_b_claims: DocumentClaims,
        min_threshold: float = 0.12
    ) -> List[ClaimPair]:
        """
        Generates best matched pairs between claims in Doc A and Doc B.
        """
        pairs = []
        pair_counter = 1

        claims_a = doc_a_claims.claims
        claims_b = doc_b_claims.claims

        # If categories match, compare
        matched_b_ids = set()

        for ca in claims_a:
            best_b = None
            best_sim = 0.0

            for cb in claims_b:
                # Calculate similarity score
                sim = cls.calculate_similarity(ca.text, cb.text, ca.key_entities, cb.key_entities)

                # Category alignment bonus
                if ca.category == cb.category:
                    sim += 0.08

                if sim > best_sim:
                    best_sim = sim
                    best_b = cb

            if best_b and best_sim >= min_threshold:
                pairs.append(ClaimPair(
                    id=f"PAIR-{pair_counter}",
                    claim_a=ca,
                    claim_b=best_b,
                    similarity=min(1.0, round(best_sim, 2)),
                    topic=ca.category if ca.category == best_b.category else f"{ca.category} / {best_b.category}"
                ))
                matched_b_ids.add(best_b.id)
                pair_counter += 1

        # Also add un-paired high confidence claims from doc_b if unmatched and topic matches
        return pairs
