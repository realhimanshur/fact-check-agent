

import os
import json
import re
import logging
from typing import List, Dict

import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaimExtractor:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set"
            )

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def extract_claims(
        self,
        text: str,
        page_count: int = 1
    ) -> List[Dict]:

        try:

            logger.info(
                "Starting claim extraction..."
            )

            prompt = self._build_extraction_prompt(
                text
            )

            response = self.model.generate_content(
                prompt
            )

            result = response.text.strip()

            result = (
                result
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            claims_data = json.loads(result)

            claims = claims_data.get(
                "claims",
                []
            )

            validated_claims = (
                self._validate_claims(
                    claims,
                    text
                )
            )

            logger.info(
                f"Extracted {len(validated_claims)} claims"
            )

            return validated_claims

        except Exception as e:

            logger.error(
                f"Claim extraction failed: {e}"
            )

            logger.info(
                "Using regex fallback..."
            )

            return self._regex_fallback_extraction(
                text
            )

    def _build_extraction_prompt(
        self,
        text: str
    ) -> str:

        return f"""
Extract all factual claims from the text.

A claim should be verifiable.

Focus on:

- Numerical claims
- Percentage claims
- Date claims
- Financial claims
- Technical claims

Return ONLY valid JSON.

Format:

{{
    "claims":[
        {{
            "claim":"text",
            "type":"NUMERICAL",
            "page":1
        }}
    ]
}}

TEXT:

{text[:15000]}
"""

    def _validate_claims(
        self,
        claims: List[Dict],
        text: str
    ) -> List[Dict]:

        validated = []

        for claim in claims:

            if (
                not claim.get("claim")
                or not claim.get("type")
            ):
                continue

            if (
                "page" not in claim
                or claim["page"] is None
            ):
                claim["page"] = (
                    self._estimate_page(
                        claim["claim"],
                        text
                    )
                )

            claim["type"] = (
                claim["type"]
                .upper()
            )

            claim_text = (
                claim["claim"]
                .strip()
            )

            if (
                len(claim_text) < 10
                or len(claim_text) > 500
            ):
                continue

            validated.append(claim)

        return validated

    def _estimate_page(
        self,
        claim: str,
        text: str
    ) -> int:

        try:

            position = text.find(
                claim[:50]
            )

            if position == -1:
                return 1

            text_before = text[:position]

            page_markers = re.findall(
                r"--- Page (\d+) ---",
                text_before
            )

            if page_markers:
                return int(
                    page_markers[-1]
                )

            return 1

        except Exception:
            return 1

    def _regex_fallback_extraction(
        self,
        text: str
    ) -> List[Dict]:

        claims = []

        numerical_pattern = (
            r"[A-Z][^.!?]*\b\d+(?:,\d{3})*"
            r"(?:\.\d+)?\s*(?:million|billion|"
            r"trillion|thousand|hundred|%|percent|"
            r"dollars?|USD|EUR)?\b[^.!?]*[.!?]"
        )

        matches = re.finditer(
            numerical_pattern,
            text
        )

        for match in matches:

            claim_text = (
                match.group().strip()
            )

            claim_type = "NUMERICAL"

            if (
                "%"
                in claim_text
                or "percent"
                in claim_text.lower()
            ):
                claim_type = "PERCENTAGE"

            elif any(
                word in claim_text.lower()
                for word in [
                    "founded",
                    "established",
                    "year",
                    "date"
                ]
            ):
                claim_type = "DATE"

            elif any(
                word in claim_text.lower()
                for word in [
                    "revenue",
                    "valuation",
                    "profit",
                    "earnings",
                    "usd"
                ]
            ):
                claim_type = "FINANCIAL"

            claims.append(
                {
                    "claim": claim_text,
                    "type": claim_type,
                    "page": self._estimate_page(
                        claim_text,
                        text
                    )
                }
            )

            if len(claims) >= 20:
                break

        logger.info(
            f"Regex extracted {len(claims)} claims"
        )

        return claims

