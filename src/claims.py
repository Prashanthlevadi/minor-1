"""
claims.py - Pydantic structured claim extraction using LLMs with intelligent fallback.
"""

import os
import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Claim(BaseModel):
    id: str = Field(description="Unique identifier for the claim, e.g. C-1")
    text: str = Field(description="The extracted atomic factual claim or assertion")
    category: str = Field(default="General", description="Category: Financial, Legal, Policy, Technical, Timeline, General")
    source_doc: str = Field(default="Document", description="Name of source document")
    location: Optional[str] = Field(default=None, description="Page or section number if applicable")
    confidence: float = Field(default=0.9, description="Confidence score between 0.0 and 1.0")
    key_entities: List[str] = Field(default_factory=list, description="Key entities, dates, figures, or key terms")


class DocumentClaims(BaseModel):
    doc_name: str
    claims: List[Claim] = Field(default_factory=list)
    total_claims: int = 0


class ClaimExtractor:
    """
    Extracts structured claims from document text using LLM APIs (Gemini/OpenAI) or heuristic NLP fallback.
    """

    @staticmethod
    def extract_with_heuristic(text: str, doc_name: str = "Document") -> DocumentClaims:
        """
        Rule-based NLP claim extractor that works 100% offline without API keys.
        Detects factual assertions, numbers, dates, obligations, and key claims.
        """
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        claims = []
        claim_id = 1

        for sentence in sentences:
            sentence_str = sentence.strip()
            if len(sentence_str) < 12:
                continue

            # Check if sentence contains factual/assertion indicators
            has_numbers = bool(re.search(r"\d+|\$\d+|\d+%", sentence_str))
            has_dates = bool(re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d\d|19\d\d|days?|months?|years?)\b", sentence_str, re.I))
            has_obligation = bool(re.search(r"\b(shall|must|will|agree|guarantee|prohibit|require|limit|provide|stipulate|include|exclude)\b", sentence_str, re.I))
            has_fact = bool(re.search(r"\b(is|are|was|were|has|have|cost|price|fee|rate|timeline|deadline|location)\b", sentence_str, re.I))

            if has_numbers or has_dates or has_obligation or (has_fact and len(sentence_str) > 20):
                # Categorize claim
                category = "General"
                if re.search(r"\$|\b(cost|price|fee|payment|dollar|usd|budget|refund|rate|penalty|salary)\b", sentence_str, re.I):
                    category = "Financial"
                elif re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|days|weeks|months|year|deadline|schedule|timeline|date|20\d\d)\b", sentence_str, re.I):
                    category = "Timeline"
                elif re.search(r"\b(shall|must|agree|contract|law|liable|indemnify|party|clause|jurisdiction|warrant)\b", sentence_str, re.I):
                    category = "Legal"
                elif re.search(r"\b(policy|term|rule|requirement|condition|allowed|permitted|standard|guideline)\b", sentence_str, re.I):
                    category = "Policy"
                elif re.search(r"\b(server|system|api|database|code|software|hardware|cpu|ram|gb|storage|bandwidth|tech)\b", sentence_str, re.I):
                    category = "Technical"

                # Extract entities (dates, figures, proper nouns)
                entities = re.findall(r"\$?\d+(?:\.\d+)?%?|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b|\b20\d\d\b", sentence_str)
                # deduplicate entities while preserving order
                unique_entities = []
                for e in entities:
                    if e not in unique_entities and len(e) > 1 and e not in ["The", "A", "In", "This", "On", "If"]:
                        unique_entities.append(e)

                claim_item = Claim(
                    id=f"C-{claim_id}",
                    text=sentence_str,
                    category=category,
                    source_doc=doc_name,
                    confidence=0.95 if (has_numbers or has_dates) else 0.85,
                    key_entities=unique_entities[:5]
                )
                claims.append(claim_item)
                claim_id += 1

                if len(claims) >= 30:  # Cap max extracted claims for performance
                    break

        return DocumentClaims(
            doc_name=doc_name,
            claims=claims,
            total_claims=len(claims)
        )

    @staticmethod
    def extract_with_gemini(text: str, api_key: str, doc_name: str = "Document") -> Optional[DocumentClaims]:
        """
        Extract claims using Google Gemini API.
        """
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            # Try gemini-1.5-flash or gemini-2.5-flash or gemini-pro
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            Extract all atomic factual claims, policy statements, quantitative details, dates, and obligations from the following text.
            For each claim, return a JSON object with:
            - id: "C-1", "C-2", etc.
            - text: The precise claim sentence or assertion.
            - category: One of ["Financial", "Legal", "Policy", "Technical", "Timeline", "General"]
            - key_entities: Array of important entities, numbers, dates, or terms in the claim.
            - confidence: float between 0.0 and 1.0

            Return ONLY a JSON array of claim objects, no markdown wrappers if possible or inside ```json block.

            Text:
            {text[:8000]}
            """

            response = model.generate_content(prompt)
            resp_text = response.text.strip()

            # Clean JSON block formatting
            if "```json" in resp_text:
                resp_text = resp_text.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0].strip()

            raw_claims = json.loads(resp_text)
            claims_list = []

            for idx, c in enumerate(raw_claims, 1):
                claims_list.append(Claim(
                    id=c.get("id", f"C-{idx}"),
                    text=c.get("text", ""),
                    category=c.get("category", "General"),
                    source_doc=doc_name,
                    confidence=float(c.get("confidence", 0.9)),
                    key_entities=c.get("key_entities", [])
                ))

            return DocumentClaims(
                doc_name=doc_name,
                claims=claims_list,
                total_claims=len(claims_list)
            )
        except Exception as e:
            # Fallback to heuristic if API call fails
            print(f"Gemini API claim extraction failed ({str(e)}), using heuristic fallback.")
            return None

    @staticmethod
    def extract_with_openai(text: str, api_key: str, doc_name: str = "Document") -> Optional[DocumentClaims]:
        """
        Extract claims using OpenAI API.
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            prompt = f"""
            Extract all atomic factual claims, commitments, numbers, dates, and policy requirements from the text.
            Return a JSON array of objects with keys: "id", "text", "category", "key_entities", "confidence".
            Categories must be: "Financial", "Legal", "Policy", "Technical", "Timeline", or "General".

            Text:
            {text[:8000]}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise NLP claim extraction assistant. Respond ONLY in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            resp_text = response.choices[0].message.content.strip()

            if "```json" in resp_text:
                resp_text = resp_text.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0].strip()

            raw_claims = json.loads(resp_text)
            claims_list = []

            for idx, c in enumerate(raw_claims, 1):
                claims_list.append(Claim(
                    id=c.get("id", f"C-{idx}"),
                    text=c.get("text", ""),
                    category=c.get("category", "General"),
                    source_doc=doc_name,
                    confidence=float(c.get("confidence", 0.9)),
                    key_entities=c.get("key_entities", [])
                ))

            return DocumentClaims(
                doc_name=doc_name,
                claims=claims_list,
                total_claims=len(claims_list)
            )
        except Exception as e:
            print(f"OpenAI API extraction failed ({str(e)}), using heuristic fallback.")
            return None

    @classmethod
    def extract_claims(
        cls,
        text: str,
        doc_name: str = "Document",
        provider: str = "auto",
        api_key: Optional[str] = None
    ) -> DocumentClaims:
        """
        Unified claim extraction entry point with provider auto-detection & fallback.
        """
        if not text or not text.strip():
            return DocumentClaims(doc_name=doc_name, claims=[], total_claims=0)

        # Check for user API keys if provided or in env
        gemini_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        openai_key = api_key or os.getenv("OPENAI_API_KEY")

        if provider in ["gemini", "auto"] and gemini_key:
            res = cls.extract_with_gemini(text, gemini_key, doc_name)
            if res:
                return res

        if provider in ["openai", "auto"] and openai_key:
            res = cls.extract_with_openai(text, openai_key, doc_name)
            if res:
                return res

        # Fallback heuristic engine
        return cls.extract_with_heuristic(text, doc_name)
