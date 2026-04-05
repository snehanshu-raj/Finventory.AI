"""LLM provider abstraction with Gemini Flash and Claude implementations."""

import abc
import base64
import json
import logging
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ── Prompt templates ───────────────────────────────────────────────────

RECEIPT_EXTRACTION_PROMPT = """Analyze this receipt image and extract structured JSON with the following schema:
{
  "merchant": {
    "name": "store name",
    "address": "store address or null",
    "phone": "phone or null"
  },
  "transaction": {
    "receiptNumber": "receipt number or null",
    "purchasedAt": "ISO 8601 datetime or null",
    "currency": "USD",
    "subtotal": 0.0,
    "tax": 0.0,
    "tip": 0.0,
    "total": 0.0,
    "paymentMethod": "card/cash/null"
  },
  "items": [
    {
      "rawText": "original text from receipt",
      "canonicalName": "normalized item name (e.g. 'eggs', 'milk', 'bread')",
      "category": "category like dairy_and_eggs, produce, meat, bakery, beverages, snacks, household, personal_care, other",
      "brand": "brand name or null",
      "quantity": 1,
      "unit": "count/kg/liter/oz/lb/pack",
      "normalizedQuantity": 1,
      "normalizedUnit": "count/kg/liter",
      "linePrice": 0.0,
      "unitPrice": 0.0,
      "confidence": 0.95,
      "isGrocery": true
    }
  ]
}

Rules:
- Normalize item names to common pantry names (e.g. "EGGS LG 12CT" -> "eggs")
- Calculate unitPrice = linePrice / quantity when possible
- Set confidence between 0.0-1.0 based on how certain you are about the extraction
- Mark items as isGrocery=false for non-food items
- Return ONLY valid JSON, no markdown formatting or explanation"""

MEAL_SUGGESTION_PROMPT_TEMPLATE = """Based on the following pantry items and constraints, suggest 3 meals.

Available pantry items:
{pantry_items}

Constraints:
- Suggest only from available items.
- Max prep time: {max_prep_minutes} minutes
- Vegetarian only: {vegetarian}
- Budget mode (use what's available): {budget_mode}

Return JSON with this schema:
{{
  "meals": [
    {{
      "title": "Meal name",
      "description": "Brief description",
      "pantryIngredientsUsed": ["item1", "item2"],
      "missingIngredients": ["item3"],
      "prepTimeMinutes": 15,
      "whySuggested": "Reason for suggesting this meal"
    }}
  ]
}}

Rules:
- Prioritize meals using available pantry items
- Keep suggestions practical and diverse
- Return ONLY valid JSON, no markdown formatting"""


# ── Abstract base class ───────────────────────────────────────────────

class LLMProvider(abc.ABC):
    """Abstract interface for LLM providers."""

    @abc.abstractmethod
    async def vision_extract(self, image_bytes: bytes, content_type: str) -> dict:
        """Send an image to the vision model and return extracted JSON."""
        ...

    @abc.abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """Send a text prompt and return the generated text."""
        ...

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Parse JSON from LLM response, stripping markdown fences or junk text."""
        cleaned = text.strip()
        
        # 1. Try to find JSON block if it's wrapped in markdown fences
        if "```" in cleaned:
            import re
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
        
        # 2. If it doesn't look like JSON (doesn't start/end with braces), 
        # try to find the first '{' and last '}'
        if not (cleaned.startswith("{") and cleaned.endswith("}")):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

        # 3. Clean trailing commas (common LLM mistake)
        import re
        cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response. Error: %s", e)
            logger.debug("Raw LLM response: %s", text)
            raise


# ── Gemini Flash Provider ─────────────────────────────────────────────

class GeminiProvider(LLMProvider):
    """Google Gemini Flash API provider."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.5-flash"

    async def vision_extract(self, image_bytes: bytes, content_type: str) -> dict:
        """Extract receipt data using Gemini Flash vision."""
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        url = f"{self.BASE_URL}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": RECEIPT_EXTRACTION_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": content_type,
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 16384,
                "response_mime_type": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        text = result["candidates"][0]["content"]["parts"][0]["text"]
        logger.info("Gemini raw response:\n%s", text)
        return self._parse_json(text)

    async def generate_text(self, prompt: str) -> str:
        """Generate text using Gemini Flash."""
        url = f"{self.BASE_URL}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 16384,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        return result["candidates"][0]["content"]["parts"][0]["text"]

        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return self._parse_json(text)


# ── Claude Provider ────────────────────────────────────────────────────

class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider."""

    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Use claude-3-5-sonnet - the latest available model
        self.model = "claude-3-5-sonnet-20241022"

    async def vision_extract(self, image_bytes: bytes, content_type: str) -> dict:
        """Extract receipt data using Claude vision."""
        logger.info(
            "Claude vision extract: image_size=%d bytes, content_type=%s",
            len(image_bytes), content_type
        )
        
        # Validate image size (Claude has limits)
        max_size = 20 * 1024 * 1024  # 20MB
        if len(image_bytes) > max_size:
            raise ValueError(f"Image too large: {len(image_bytes)} bytes (max {max_size})")
        
        # Validate content type
        valid_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        if content_type not in valid_types:
            logger.warning("Invalid content_type: %s, using image/jpeg", content_type)
            content_type = "image/jpeg"
        
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        logger.info("Base64 encoded image: %d chars", len(b64_image))
        
        url = f"{self.BASE_URL}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 16384,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": b64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": RECEIPT_EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    logger.error(
                        "Claude API error %d: %s",
                        response.status_code, response.text
                    )
                response.raise_for_status()
                result = response.json()

            text = result["content"][0]["text"]
            return self._parse_json(text)
        except Exception as e:
            logger.exception("Claude vision extraction failed: %s", e)
            raise

    async def generate_text(self, prompt: str) -> str:
        """Generate text using Claude."""
        url = f"{self.BASE_URL}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 16384,
            "messages": [{"role": "user", "content": prompt}],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

        return result["content"][0]["text"]


# ── Mock Provider ──────────────────────────────────────────────────────

class MockProvider(LLMProvider):
    """Mock provider returning sample data for local development."""

    async def vision_extract(self, image_bytes: bytes, content_type: str) -> dict:
        """Return sample extracted receipt data."""
        logger.info("MockProvider: returning sample receipt extraction")
        return {
            "merchant": {
                "name": "Sample Grocery Store",
                "address": "123 Main St, Anytown, USA",
                "phone": "(555) 123-4567",
            },
            "transaction": {
                "receiptNumber": "MOCK-001",
                "purchasedAt": "2026-04-02T18:10:00Z",
                "currency": "USD",
                "subtotal": 38.40,
                "tax": 3.78,
                "tip": 0,
                "total": 42.18,
                "paymentMethod": "card",
            },
            "items": [
                {
                    "rawText": "EGGS LG 12CT",
                    "canonicalName": "eggs",
                    "category": "dairy_and_eggs",
                    "brand": None,
                    "quantity": 12,
                    "unit": "count",
                    "normalizedQuantity": 12,
                    "normalizedUnit": "count",
                    "linePrice": 4.29,
                    "unitPrice": 0.3575,
                    "confidence": 0.94,
                    "isGrocery": True,
                },
                {
                    "rawText": "WHOLE MILK 1GAL",
                    "canonicalName": "milk",
                    "category": "dairy_and_eggs",
                    "brand": None,
                    "quantity": 1,
                    "unit": "gallon",
                    "normalizedQuantity": 3.785,
                    "normalizedUnit": "liter",
                    "linePrice": 5.49,
                    "unitPrice": 1.45,
                    "confidence": 0.92,
                    "isGrocery": True,
                },
                {
                    "rawText": "WHEAT BREAD",
                    "canonicalName": "bread",
                    "category": "bakery",
                    "brand": "Wonder",
                    "quantity": 1,
                    "unit": "count",
                    "normalizedQuantity": 1,
                    "normalizedUnit": "count",
                    "linePrice": 3.99,
                    "unitPrice": 3.99,
                    "confidence": 0.96,
                    "isGrocery": True,
                },
                {
                    "rawText": "BNLS CHICKEN BRST",
                    "canonicalName": "chicken breast",
                    "category": "meat",
                    "brand": None,
                    "quantity": 1.5,
                    "unit": "lb",
                    "normalizedQuantity": 0.68,
                    "normalizedUnit": "kg",
                    "linePrice": 8.99,
                    "unitPrice": 5.99,
                    "confidence": 0.88,
                    "isGrocery": True,
                },
                {
                    "rawText": "BASMATI RICE 5LB",
                    "canonicalName": "rice",
                    "category": "grains",
                    "brand": None,
                    "quantity": 5,
                    "unit": "lb",
                    "normalizedQuantity": 2.27,
                    "normalizedUnit": "kg",
                    "linePrice": 7.99,
                    "unitPrice": 1.60,
                    "confidence": 0.91,
                    "isGrocery": True,
                },
                {
                    "rawText": "ATTA WHOLEWHEAT 10LB",
                    "canonicalName": "atta",
                    "category": "grains",
                    "brand": None,
                    "quantity": 10,
                    "unit": "lb",
                    "normalizedQuantity": 4.54,
                    "normalizedUnit": "kg",
                    "linePrice": 7.65,
                    "unitPrice": 0.765,
                    "confidence": 0.90,
                    "isGrocery": True,
                },
            ],
        }

    async def generate_text(self, prompt: str) -> str:
        """Return sample meal suggestions."""
        logger.info("MockProvider: returning sample meal suggestions")
        return json.dumps({
            "meals": [
                {
                    "title": "Simple Egg Fried Rice",
                    "description": "Quick and easy egg fried rice using pantry staples.",
                    "pantryIngredientsUsed": ["rice", "eggs"],
                    "missingIngredients": ["soy sauce", "green onions"],
                    "prepTimeMinutes": 15,
                    "whySuggested": "Uses available rice and eggs from your pantry.",
                },
                {
                    "title": "Chicken Chapati Wrap",
                    "description": "Grilled chicken breast wrapped in fresh atta chapati.",
                    "pantryIngredientsUsed": ["chicken breast", "atta"],
                    "missingIngredients": ["onion", "tomato"],
                    "prepTimeMinutes": 20,
                    "whySuggested": "Great use of chicken and atta before they run low.",
                },
                {
                    "title": "Bread and Egg Toast",
                    "description": "Classic buttered egg toast with wheat bread.",
                    "pantryIngredientsUsed": ["bread", "eggs", "milk"],
                    "missingIngredients": ["butter"],
                    "prepTimeMinutes": 10,
                    "whySuggested": "Quick breakfast using items you have on hand.",
                },
            ]
        })


# ── Factory ────────────────────────────────────────────────────────────

def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance."""
    provider_name = settings.llm_provider.lower()
    if provider_name == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return GeminiProvider(api_key=settings.gemini_api_key)
    elif provider_name == "claude":
        if not settings.claude_api_key:
            raise ValueError("CLAUDE_API_KEY is required when LLM_PROVIDER=claude")
        return ClaudeProvider(api_key=settings.claude_api_key)
    elif provider_name == "mock":
        return MockProvider()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider_name}. Use 'gemini', 'claude', or 'mock'.")
