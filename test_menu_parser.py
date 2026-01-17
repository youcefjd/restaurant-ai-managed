#!/usr/bin/env python3
"""
Simple test script to verify menu parser migration from Ollama to Gemini.
Tests text-based menu parsing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.menu_parser import menu_parser


async def test_menu_parser():
    """Test the menu parser with a sample text menu."""
    
    print("🧪 Testing Menu Parser Migration (Ollama → Gemini)")
    print("=" * 60)
    
    # Check if Gemini is configured
    if not menu_parser.enabled:
        print("❌ ERROR: Menu parser is not enabled")
        print(f"   Please ensure GOOGLE_AI_API_KEY is set in your environment")
        return False
    
    print(f"✅ Menu parser initialized")
    print(f"   Model: {menu_parser.gemini_model}")
    print()
    
    # Sample menu text
    sample_menu = """
    RESTAURANT MENU
    
    Appetizers
    - Caesar Salad - Fresh romaine lettuce with Caesar dressing - $8.99
    - Buffalo Wings - Spicy chicken wings with blue cheese - $12.99 [gluten_free]
    
    Main Courses
    - Grilled Salmon - Atlantic salmon with vegetables - $18.99 [gluten_free]
    - Beef Burger - Classic burger with fries - $14.99
    - Vegetarian Pasta - Penne with marinara sauce - $12.99 [vegetarian]
    
    Desserts
    - Chocolate Cake - Rich chocolate cake - $6.99
    - Ice Cream - Vanilla or chocolate - $4.99
    """
    
    print("📝 Testing text menu parsing...")
    try:
        result = await menu_parser.parse_menu(input_data=sample_menu)
        
        print("✅ Menu parsed successfully!")
        print()
        print("📊 Parsed Structure:")
        print(f"   Menu Name: {result.get('name', 'N/A')}")
        print(f"   Categories: {len(result.get('categories', []))}")
        
        for category in result.get('categories', []):
            print(f"   - {category.get('name')}: {len(category.get('items', []))} items")
            for item in category.get('items', [])[:3]:  # Show first 3 items
                price = item.get('price_cents', 0) / 100
                tags = item.get('dietary_tags', [])
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                print(f"     • {item.get('name')} - ${price:.2f}{tag_str}")
        
        print()
        print("✅ Test PASSED - Menu parser is working with Gemini!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Menu parsing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("GOOGLE_AI_API_KEY"):
        print("❌ ERROR: GOOGLE_AI_API_KEY environment variable not set")
        print("   Please set it before running this test")
        sys.exit(1)
    
    success = asyncio.run(test_menu_parser())
    sys.exit(0 if success else 1)
