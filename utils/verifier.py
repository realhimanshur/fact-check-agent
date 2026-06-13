import os
import json
import logging
from typing import Dict, List
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FactVerifier:
    """
    Verifies factual claims against web search results
    Uses Gemini to analyze evidence and generate verdicts
    """

    def __init__(self, search_engine):
        """
        Initialize fact verifier

        Args:
            search_engine: SearchEngine instance for web searches
        """

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.search_engine = search_engine

    def verify_claim(self, claim_data: Dict) -> Dict:
        """
        Verify a single claim
        """

        try:
            claim = claim_data["claim"]

            logger.info(f"Verifying claim: {claim[:100]}...")

            search_results = self._search_for_evidence(claim)

            if not search_results:
                return self._create_error_result(
                    claim_data,
                    "No search results found"
                )

            verification = self._analyze_evidence(
                claim,
                search_results
            )

            result = {
                "claim": claim,
                "type": claim_data["type"],
                "page": claim_data.get("page", 1),
                "verdict": verification.get("verdict", "ERROR"),
                "confidence": verification.get("confidence", 0),
                "reasoning": verification.get("reasoning", ""),
                "corrected_fact": verification.get("corrected_fact"),
                "evidence": self._extract_evidence(search_results),
                "sources": self._extract_sources(search_results)
            }

            return result

        except Exception as e:
            logger.error(f"Error verifying claim: {str(e)}")

            return self._create_error_result(
                claim_data,
                str(e)
            )

    def _search_for_evidence(self, claim: str) -> List[Dict]:

        query = self._create_search_query(claim)

        return self.search_engine.search(
            query,
            max_results=5
        )

    def _create_search_query(self, claim: str) -> str:
        return claim

    def _analyze_evidence(
        self,
        claim: str,
        search_results: List[Dict]
    ) -> Dict:

        try:

            evidence_text = self._build_evidence_context(
                search_results
            )

            prompt = f"""
You are an expert fact-checker.

CLAIM:
{claim}

EVIDENCE:
{evidence_text}

Determine:

1. VERIFIED
2. INACCURATE
3. FALSE

Return ONLY valid JSON:

{{
  "verdict":"VERIFIED",
  "confidence":95,
  "reasoning":"Short explanation",
  "corrected_fact":null
}}
"""

            response = self.model.generate_content(prompt)

            result = response.text.strip()

            result = (
                result
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            verification = json.loads(result)

            valid_verdicts = [
                "VERIFIED",
                "INACCURATE",
                "FALSE"
            ]

            if verification.get("verdict") not in valid_verdicts:
                verification["verdict"] = "FALSE"

            confidence = verification.get(
                "confidence",
                50
            )

            verification["confidence"] = max(
                0,
                min(100, confidence)
            )

            return verification

        except Exception as e:

            logger.error(
                f"Error analyzing evidence: {str(e)}"
            )

            return {
                "verdict": "ERROR",
                "confidence": 0,
                "reasoning": str(e),
                "corrected_fact": None
            }

    def _build_evidence_context(
        self,
        search_results: List[Dict]
    ) -> str:

        evidence_parts = []

        for idx, result in enumerate(
            search_results[:5],
            1
        ):

            evidence_parts.append(
                f"""
Source {idx}
Title: {result.get('title','')}
URL: {result.get('url','')}
Content: {result.get('snippet','')}
"""
            )

        return "\n".join(evidence_parts)

    def _extract_evidence(
        self,
        search_results: List[Dict]
    ) -> List[str]:

        evidence = []

        for result in search_results[:3]:

            snippet = result.get(
                "snippet",
                ""
            )

            if snippet:
                evidence.append(snippet)

        return evidence

    def _extract_sources(
        self,
        search_results: List[Dict]
    ) -> List[Dict]:

        sources = []

        for result in search_results[:5]:

            title = result.get("title", "")
            url = result.get("url", "")

            if title and url:

                sources.append(
                    {
                        "title": title,
                        "url": url
                    }
                )

        return sources

    def _create_error_result(
        self,
        claim_data: Dict,
        error_msg: str
    ) -> Dict:

        return {
            "claim": claim_data["claim"],
            "type": claim_data["type"],
            "page": claim_data.get("page", 1),
            "verdict": "ERROR",
            "confidence": 0,
            "reasoning": error_msg,
            "corrected_fact": None,
            "evidence": [],
            "sources": []
        }
