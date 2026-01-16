"""
Menu parsing service using LLM to extract menu data from various formats.

Supports parsing menus from:
- JSON format
- Plain text
- Images (menu photos)

Uses Ollama for LLM processing.
"""

import os
import json
import base64
import logging
import requests
from typing import Dict, Any, List, Optional
from io import BytesIO

try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("PyPDF2 not installed, PDF support disabled")

logger = logging.getLogger(__name__)


class MenuParser:
    """Service for parsing menu data from various input formats using Ollama."""

    def __init__(self):
        """Initialize the menu parser with Ollama."""
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.ollama_vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava")
        self.enabled = True

        # Test Ollama connection
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info(f"Ollama connection successful, using model: {self.ollama_model} for text, {self.ollama_vision_model} for images")
            else:
                logger.warning("Ollama server not responding, menu parsing may not work")
                self.enabled = False
        except Exception as e:
            logger.warning(f"Could not connect to Ollama at {self.ollama_url}: {str(e)}")
            self.enabled = False

    async def parse_menu(
        self,
        input_data: Optional[str] = None,
        image_data: Optional[bytes] = None,
        image_type: Optional[str] = None,
        pdf_data: Optional[bytes] = None,
        image_list: Optional[List[bytes]] = None,
        image_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Parse menu data from JSON, text, image, PDF, or multiple images.

        Args:
            input_data: JSON string or plain text containing menu data
            image_data: Binary image data (menu photo) - single image
            image_type: Image MIME type (e.g., 'image/jpeg', 'image/png')
            pdf_data: Binary PDF data
            image_list: List of binary image data (multiple images)
            image_types: List of image MIME types for image_list

        Returns:
            Dictionary with parsed menu structure (merged if multiple images)
        """
        # If input_data looks like JSON, try to parse it directly
        if input_data:
            try:
                menu_json = json.loads(input_data)
                # Validate and normalize the JSON structure
                return self._normalize_json_menu(menu_json)
            except json.JSONDecodeError:
                # Not JSON, treat as plain text
                pass

        # Handle PDF first (extract text from PDF)
        if pdf_data:
            if not PDF_SUPPORT:
                raise ValueError("PDF support not available. Please install PyPDF2.")
            text_from_pdf = self._extract_text_from_pdf(pdf_data)
            if not text_from_pdf.strip():
                raise ValueError("Could not extract text from PDF")
            input_data = text_from_pdf

        # Handle multiple images (process and merge)
        if image_list and len(image_list) > 0:
            if not self.enabled:
                raise ValueError(
                    f"Ollama is not available at {self.ollama_url}. "
                    "Please ensure Ollama is running and accessible."
                )
            return await self._parse_menu_from_multiple_images(image_list, image_types or [])

        # Use LLM to parse text or single image
        if not self.enabled and (input_data or image_data):
            raise ValueError(
                f"Ollama is not available at {self.ollama_url}. "
                "Please ensure Ollama is running and accessible."
            )

        try:
            if image_data:
                return await self._parse_menu_from_image(image_data, image_type)
            elif input_data:
                return await self._parse_menu_from_text(input_data)
            else:
                raise ValueError("Must provide input_data, image_data, pdf_data, or image_list")
        except Exception as e:
            logger.error(f"Error parsing menu: {str(e)}")
            raise

    def _normalize_json_menu(self, menu_json: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate JSON menu structure."""
        normalized = {
            "name": menu_json.get("name", "Menu"),
            "description": menu_json.get("description"),
            "categories": []
        }

        categories = menu_json.get("categories", [])
        if not isinstance(categories, list):
            raise ValueError("Menu JSON must contain a 'categories' array")

        for idx, category in enumerate(categories):
            if not isinstance(category, dict):
                continue

            normalized_category = {
                "name": category.get("name", f"Category {idx + 1}"),
                "description": category.get("description"),
                "display_order": category.get("display_order", idx),
                "items": []
            }

            items = category.get("items", [])
            if not isinstance(items, list):
                continue

            for item_idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue

                # Handle price - can be in dollars or cents
                price = item.get("price", 0) or item.get("price_cents", 0)
                if isinstance(price, (int, float)):
                    price_cents = int(price * 100) if price < 1000 else int(price)
                else:
                    price_cents = 0

                normalized_item = {
                    "name": item.get("name", f"Item {item_idx + 1}"),
                    "description": item.get("description"),
                    "price_cents": price_cents,
                    "dietary_tags": item.get("dietary_tags", []),
                    "preparation_time_minutes": item.get("preparation_time_minutes"),
                    "display_order": item.get("display_order", item_idx)
                }

                normalized_category["items"].append(normalized_item)

            normalized["categories"].append(normalized_category)

        return normalized

    async def _parse_menu_from_text(self, text: str) -> Dict[str, Any]:
        """Parse menu from plain text using Ollama."""
        system_prompt = """You are a menu parsing expert. Extract menu information from the provided text and return a structured JSON format.

The output must be valid JSON with this structure:
{
    "name": "Menu Name",
    "description": "Optional menu description",
    "categories": [
        {
            "name": "Category Name",
            "description": "Optional category description",
            "display_order": 0,
            "items": [
                {
                    "name": "Item Name",
                    "description": "Item description",
                    "price_cents": 1000,
                    "dietary_tags": ["vegetarian", "vegan", "gluten_free", etc.],
                    "preparation_time_minutes": 20
                }
            ]
        }
    ]
}

Important rules:
- Extract all menu items and organize them into logical categories (Appetizers, Main Courses, Desserts, etc.)
- Convert all prices to cents (e.g., $10.99 = 1099)
- If price is missing, set to 0
- Extract dietary information if mentioned (vegetarian, vegan, gluten-free, etc.)
- Be thorough and extract all items, even if the format is messy
- Return ONLY valid JSON, no additional text"""

        user_message = f"""Please parse this menu text and extract all menu items, prices, and categories:

{text}

Return the structured JSON format as specified."""

        full_prompt = f"{system_prompt}\n\n{user_message}"

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent JSON
                    }
                },
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

            ai_response = response.json().get("response", "")
            if not ai_response:
                raise ValueError("Empty response from Ollama")

            # Extract JSON from response
            json_text = self._extract_json_from_response(ai_response)
            menu_data = json.loads(json_text)
            return self._normalize_json_menu(menu_data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {str(e)}")
            raise ValueError(f"Failed to parse menu JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing menu from text: {str(e)}")
            raise ValueError(f"Failed to parse menu from text: {str(e)}")

    async def _parse_menu_from_image(self, image_data: bytes, image_type: str) -> Dict[str, Any]:
        """Parse menu from image using Ollama vision model."""
        # Convert image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        system_prompt = """You are a menu parsing expert. Analyze the menu image and extract all menu information, including items, prices, categories, and descriptions.

The output must be valid JSON with this structure:
{
    "name": "Menu Name",
    "description": "Optional menu description",
    "categories": [
        {
            "name": "Category Name",
            "description": "Optional category description",
            "display_order": 0,
            "items": [
                {
                    "name": "Item Name",
                    "description": "Item description",
                    "price_cents": 1000,
                    "dietary_tags": ["vegetarian", "vegan", "gluten_free", etc.],
                    "preparation_time_minutes": 20
                }
            ]
        }
    ]
}

Important rules:
- Read all text from the image carefully
- Extract all menu items and organize them into logical categories
- Convert all prices to cents (e.g., $10.99 = 1099)
- If price format is unclear, make best estimate
- Extract dietary information if visible (vegetarian, vegan, gluten-free symbols, etc.)
- Be thorough and extract everything you can see
- Return ONLY valid JSON, no additional text"""

        user_message = "Please analyze this menu image and extract all menu items, prices, categories, and descriptions. Return the structured JSON format as specified."

        try:
            # Use /api/chat endpoint for vision models
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": user_message,
                            "images": [base64_image]
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent JSON
                    }
                },
                timeout=120  # Longer timeout for vision processing
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

            ai_response = response.json().get("message", {}).get("content", "")
            if not ai_response:
                raise ValueError("Empty response from Ollama")

            # Extract JSON from response
            json_text = self._extract_json_from_response(ai_response)
            menu_data = json.loads(json_text)
            return self._normalize_json_menu(menu_data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {str(e)}")
            raise ValueError(f"Failed to parse menu JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing menu from image: {str(e)}")
            raise ValueError(f"Failed to parse menu from image: {str(e)}")

    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from LLM response (might be wrapped in markdown code blocks)."""
        # Remove markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end > start:
                return response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end > start:
                return response_text[start:end].strip()
        
        # Try to find JSON object boundaries
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            return response_text[start:end]
        
        # If no JSON found, return original (will fail JSON parsing)
        return response_text

    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = BytesIO(pdf_data)
            reader = PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    async def _parse_menu_from_multiple_images(self, image_list: List[bytes], image_types: List[str]) -> Dict[str, Any]:
        """Parse menu from multiple images by processing each and merging results."""
        all_categories = []
        menu_name = None
        menu_description = None
        
        for idx, image_data in enumerate(image_list):
            image_type = image_types[idx] if idx < len(image_types) else "image/jpeg"
            try:
                parsed_menu = await self._parse_menu_from_image(image_data, image_type)
                
                # Use first menu's name/description
                if not menu_name:
                    menu_name = parsed_menu.get("name")
                if not menu_description:
                    menu_description = parsed_menu.get("description")
                
                # Merge categories (avoid duplicates by name)
                for category in parsed_menu.get("categories", []):
                    # Check if category already exists
                    existing_cat = next(
                        (c for c in all_categories if c.get("name") == category.get("name")),
                        None
                    )
                    if existing_cat:
                        # Merge items into existing category
                        existing_items = {item.get("name"): item for item in existing_cat.get("items", [])}
                        for item in category.get("items", []):
                            if item.get("name") not in existing_items:
                                existing_cat["items"].append(item)
                    else:
                        # Create a copy of the category to avoid modifying the original
                        new_category = {
                            "name": category.get("name"),
                            "description": category.get("description"),
                            "display_order": category.get("display_order", len(all_categories)),
                            "items": list(category.get("items", []))
                        }
                        all_categories.append(new_category)
            except Exception as e:
                logger.warning(f"Error parsing image {idx + 1}: {str(e)}")
                # Continue with other images
                continue
        
        if not all_categories:
            raise ValueError("Could not parse any menu items from the provided images")
        
        return {
            "name": menu_name or "Imported Menu",
            "description": menu_description,
            "categories": all_categories
        }


# Global instance
menu_parser = MenuParser()
