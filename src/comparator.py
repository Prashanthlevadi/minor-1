"""
comparator.py - Deep contradiction analysis, severity grading, and explanation engine.
"""

import os
import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.claims import Claim
from src.matcher import ClaimPair


class ContradictionResult(BaseModel):
    pair_id: str
    claim_a: Claim
    claim_b: Claim
    is_contradiction: bool
    severity: str = Field(description="HIGH, MEDIUM, LOW, or CONSISTENT")
    category: str
    explanation: str = Field(description="Detailed explanation of the contradiction or alignment")
    conflict_detail: str = Field(default="", description="Key conflicting values or terms, e.g. '$50,000 vs $100,000'")
    recommendation: str = Field(default="", description="Suggested resolution or audit step")
    confidence: float = Field(default=0.9)


class ContradictionSummary(BaseModel):
    total_pairs_analyzed: int
    contradictions_found: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    consistent_count: int
    overall_consistency_score: float  # Percentage 0-100%
    results: List[ContradictionResult]


class ContradictionComparator:
    """
    Compares aligned claim pairs to classify contradictions, grade severity, and provide explanations.
    """

    @staticmethod
    def analyze_pair_heuristic(pair: ClaimPair) -> ContradictionResult:
        """
        Rule-based NLP engine for detecting numerical, logical, and temporal contradictions.
        """
        ca = pair.claim_a
        cb = pair.claim_b

        text_a = ca.text.lower()
        text_b = cb.text.lower()

        # 1. Extract numbers and figures from both
        nums_a = re.findall(r"\$?\d+(?:\.\d+)?%?", text_a)
        nums_b = re.findall(r"\$?\d+(?:\.\d+)?%?", text_b)

        # Check opposing keywords
        opposites = [
            ("allow", "prohibit"), ("allowed", "forbidden"), ("permitted", "prohibited"),
            ("included", "excluded"), ("mandatory", "optional"), ("required", "voluntary"),
            ("free", "charge"), ("always", "never"), ("increase", "decrease"),
            ("full", "partial"), ("accepted", "rejected"), ("eligible", "ineligible"),
            ("valid", "invalid"), ("active", "terminated"), ("refundable", "non-refundable"),
            ("unlimited", "limited"), ("maximum", "minimum")
        ]

        has_opposite = False
        opp_detail = ""
        for w1, w2 in opposites:
            if (w1 in text_a and w2 in text_b) or (w2 in text_a and w1 in text_b):
                has_opposite = True
                opp_detail = f"'{w1}' in Doc A vs '{w2}' in Doc B"
                break

        # Check numerical discrepancy
        num_conflict = False
        num_detail = ""
        if nums_a and nums_b and nums_a != nums_b:
            # If same context but different numbers
            common_words = set(re.sub(r"[^\w\s]", "", text_a).split()).intersection(
                set(re.sub(r"[^\w\s]", "", text_b).split())
            ) - {"the", "a", "is", "in", "to", "for", "and", "or", "of", "with"}

            if len(common_words) >= 2:
                num_conflict = True
                num_detail = f"Doc A states {', '.join(nums_a)} while Doc B states {', '.join(nums_b)}"

        # Severity Classification
        if has_opposite or num_conflict:
            severity = "HIGH"
            is_contra = True
            conflict_str = opp_detail or num_detail
            explanation = (
                f"Direct contradiction detected. Document A states: \"{ca.text}\". "
                f"Document B states: \"{cb.text}\". {conflict_str}."
            )
            rec = "Reconcile conflicting legal/financial commitments before finalizing agreements."
            conf = 0.92
        elif (("not" in text_a and "not" not in text_b) or ("not" in text_b and "not" not in text_a)) and pair.similarity > 0.4:
            severity = "HIGH"
            is_contra = True
            conflict_str = "Negation mismatch ('not' present in one statement)"
            explanation = (
                f"Negation contradiction detected. Doc A says: \"{ca.text}\" vs Doc B says: \"{cb.text}\"."
            )
            rec = "Verify whether the negative clause was added in revision or is an oversight."
            conf = 0.88
        elif pair.similarity > 0.35 and (set(nums_a) != set(nums_b) and (nums_a or nums_b)):
            severity = "MEDIUM"
            is_contra = True
            conflict_str = f"Specific figures diverge: {nums_a} vs {nums_b}"
            explanation = (
                f"Discrepancy in specifications or metrics. Doc A: \"{ca.text}\" vs Doc B: \"{cb.text}\"."
            )
            rec = "Confirm exact numerical baseline across team documentation."
            conf = 0.80
        elif pair.similarity > 0.45:
            # Check minor differences
            words_a = set(text_a.split())
            words_b = set(text_b.split())
            diff = words_a.symmetric_difference(words_b)
            if len(diff) > 4:
                severity = "LOW"
                is_contra = False
                conflict_str = "Nuanced wording variations"
                explanation = (
                    f"Minor wording difference. Doc A: \"{ca.text}\" vs Doc B: \"{cb.text}\"."
                )
                rec = "Ensure standardized terminology across both documents."
                conf = 0.85
            else:
                severity = "CONSISTENT"
                is_contra = False
                conflict_str = "Consistent statements"
                explanation = (
                    f"Both documents align on this point. Doc A: \"{ca.text}\" agrees with Doc B: \"{cb.text}\"."
                )
                rec = "No action required."
                conf = 0.95
        else:
            severity = "CONSISTENT"
            is_contra = False
            conflict_str = "No major contradiction"
            explanation = f"Statements appear mutually compatible."
            rec = "No action needed."
            conf = 0.75

        return ContradictionResult(
            pair_id=pair.id,
            claim_a=ca,
            claim_b=cb,
            is_contradiction=is_contra,
            severity=severity,
            category=pair.topic,
            explanation=explanation,
            conflict_detail=conflict_str,
            recommendation=rec,
            confidence=conf
        )

    @staticmethod
    def analyze_pair_gemini(pair: ClaimPair, api_key: str) -> Optional[ContradictionResult]:
        """
        Analyze claim pair with Google Gemini API.
        """
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            Analyze the following two claims from Document A and Document B for logical or factual contradictions:

            Claim A (Doc A): "{pair.claim_a.text}"
            Claim B (Doc B): "{pair.claim_b.text}"

            Determine:
            1. is_contradiction: true if they conflict, false if consistent/complementary.
            2. severity: "HIGH" (direct contradiction/opposite numbers/facts), "MEDIUM" (partial discrepancy/timeline shift), "LOW" (minor terminology difference), or "CONSISTENT" (no contradiction).
            3. conflict_detail: Short highlight of conflicting terms/numbers (e.g. "$50k vs $100k").
            4. explanation: Detailed clear explanation of why they contradict or align.
            5. recommendation: Actionable recommendation to resolve the issue.
            6. confidence: float 0.0 to 1.0

            Return ONLY valid JSON matching this schema:
            {{
              "is_contradiction": boolean,
              "severity": string,
              "conflict_detail": string,
              "explanation": string,
              "recommendation": string,
              "confidence": float
            }}
            """

            response = model.generate_content(prompt)
            resp_text = response.text.strip()

            if "```json" in resp_text:
                resp_text = resp_text.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0].strip()

            data = json.loads(resp_text)

            return ContradictionResult(
                pair_id=pair.id,
                claim_a=pair.claim_a,
                claim_b=pair.claim_b,
                is_contradiction=bool(data.get("is_contradiction", False)),
                severity=data.get("severity", "CONSISTENT").upper(),
                category=pair.topic,
                explanation=data.get("explanation", ""),
                conflict_detail=data.get("conflict_detail", ""),
                recommendation=data.get("recommendation", ""),
                confidence=float(data.get("confidence", 0.9))
            )
        except Exception as e:
            print(f"Gemini comparator call failed ({str(e)}), using heuristic fallback.")
            return None

    @staticmethod
    def analyze_pair_openai(pair: ClaimPair, api_key: str) -> Optional[ContradictionResult]:
        """
        Analyze claim pair with OpenAI API.
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            prompt = f"""
            Compare these two claims:
            Claim A: "{pair.claim_a.text}"
            Claim B: "{pair.claim_b.text}"

            Return JSON with keys:
            "is_contradiction" (bool), "severity" ("HIGH", "MEDIUM", "LOW", "CONSISTENT"), "conflict_detail" (string), "explanation" (string), "recommendation" (string), "confidence" (float).
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert legal and document contradiction analyst. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            resp_text = response.choices[0].message.content.strip()

            if "```json" in resp_text:
                resp_text = resp_text.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0].strip()

            data = json.loads(resp_text)

            return ContradictionResult(
                pair_id=pair.id,
                claim_a=pair.claim_a,
                claim_b=pair.claim_b,
                is_contradiction=bool(data.get("is_contradiction", False)),
                severity=data.get("severity", "CONSISTENT").upper(),
                category=pair.topic,
                explanation=data.get("explanation", ""),
                conflict_detail=data.get("conflict_detail", ""),
                recommendation=data.get("recommendation", ""),
                confidence=float(data.get("confidence", 0.9))
            )
        except Exception as e:
            print(f"OpenAI comparator call failed ({str(e)}), using heuristic fallback.")
            return None

    @classmethod
    def compare_pairs(
        cls,
        pairs: List[ClaimPair],
        provider: str = "auto",
        api_key: Optional[str] = None
    ) -> ContradictionSummary:
        """
        Runs contradiction analysis on all matched pairs and returns aggregated summary stats.
        """
        results = []
        gemini_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        openai_key = api_key or os.getenv("OPENAI_API_KEY")

        for pair in pairs:
            res = None
            if provider in ["gemini", "auto"] and gemini_key:
                res = cls.analyze_pair_gemini(pair, gemini_key)
            if not res and provider in ["openai", "auto"] and openai_key:
                res = cls.analyze_pair_openai(pair, openai_key)
            if not res:
                res = cls.analyze_pair_heuristic(pair)

            results.append(res)

        # Calculate metrics
        high_cnt = sum(1 for r in results if r.severity == "HIGH")
        med_cnt = sum(1 for r in results if r.severity == "MEDIUM")
        low_cnt = sum(1 for r in results if r.severity == "LOW")
        cons_cnt = sum(1 for r in results if r.severity == "CONSISTENT")
        contradictions_total = high_cnt + med_cnt + low_cnt

        total_pairs = len(results)
        if total_pairs > 0:
            consistency_score = round((cons_cnt / total_pairs) * 100, 1)
        else:
            consistency_score = 100.0

        return ContradictionSummary(
            total_pairs_analyzed=total_pairs,
            contradictions_found=contradictions_total,
            high_severity_count=high_cnt,
            medium_severity_count=med_cnt,
            low_severity_count=low_cnt,
            consistent_count=cons_cnt,
            overall_consistency_score=consistency_score,
            results=results
        )
