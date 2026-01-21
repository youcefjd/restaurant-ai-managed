#!/usr/bin/env python3
"""
Test script for Retell AI Custom Tool endpoints.

Run with: python test_retell_tools.py

Make sure the backend is running first:
  cd backend && uvicorn main:app --reload
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/mcp-tools"


def print_result(name: str, response: requests.Response):
    """Pretty print test results."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()


def test_identify_restaurant():
    """Test identify restaurant by phone number."""
    # Simulate Retell's call object format
    payload = {
        "call": {
            "to_number": "+18329254593",  # Replace with your Retell phone number
            "from_number": "+15551234567"
        },
        "args": {}
    }
    response = requests.post(f"{BASE_URL}/identify-restaurant", json=payload)
    print_result("Identify Restaurant (POST)", response)
    return response.json() if response.status_code == 200 else None


def test_get_restaurant_by_phone():
    """Test GET endpoint for restaurant lookup."""
    phone = "+18329254593"  # Replace with your Retell phone number
    response = requests.get(f"{BASE_URL}/get-restaurant-by-phone", params={"phone_number": phone})
    print_result("Get Restaurant by Phone (GET)", response)
    return response.json() if response.status_code == 200 else None


def test_get_menu(restaurant_id: int):
    """Test get menu endpoint."""
    # Test GET version
    response = requests.get(f"{BASE_URL}/get-menu", params={"restaurant_id": restaurant_id})
    print_result("Get Menu (GET)", response)

    # Test POST version (Retell format)
    payload = {
        "args": {
            "restaurant_id": restaurant_id
        }
    }
    response = requests.post(f"{BASE_URL}/tools/get-menu", json=payload)
    print_result("Get Menu (POST - Retell Tool)", response)
    return response.json() if response.status_code == 200 else None


def test_check_hours(restaurant_id: int):
    """Test check hours endpoint."""
    payload = {
        "args": {
            "restaurant_id": restaurant_id
        }
    }
    response = requests.post(f"{BASE_URL}/tools/check-hours", json=payload)
    print_result("Check Hours (POST - Retell Tool)", response)
    return response.json() if response.status_code == 200 else None


def test_check_item(restaurant_id: int, item_name: str):
    """Test check item availability endpoint."""
    payload = {
        "args": {
            "restaurant_id": restaurant_id,
            "item_name": item_name
        }
    }
    response = requests.post(f"{BASE_URL}/tools/check-item", json=payload)
    print_result(f"Check Item: '{item_name}' (POST - Retell Tool)", response)
    return response.json() if response.status_code == 200 else None


def test_create_order(restaurant_id: int):
    """Test create order endpoint."""
    payload = {
        "args": {
            "restaurant_id": restaurant_id,
            "customer_name": "John Test",
            "customer_phone": "+15551234567",
            "order_type": "pickup",
            "items": [
                {"item_name": "chicken", "quantity": 2},  # Will match partial name
            ],
            "special_instructions": "Extra napkins please"
        }
    }
    response = requests.post(f"{BASE_URL}/tools/create-order", json=payload)
    print_result("Create Order (POST - Retell Tool)", response)
    return response.json() if response.status_code == 200 else None


def test_get_restaurant_info(restaurant_id: int):
    """Test get restaurant info endpoint."""
    response = requests.get(f"{BASE_URL}/get-restaurant-info", params={"restaurant_id": restaurant_id})
    print_result("Get Restaurant Info (GET)", response)
    return response.json() if response.status_code == 200 else None


def main():
    print("\n" + "="*60)
    print("  RETELL AI CUSTOM TOOLS - ENDPOINT TESTS")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure backend is running: uvicorn backend.main:app --reload\n")

    # Test 1: Identify restaurant
    result = test_identify_restaurant()
    restaurant_id = result.get("restaurant_id") if result and result.get("found") else None

    if not restaurant_id:
        # Try GET version
        result = test_get_restaurant_by_phone()
        restaurant_id = result.get("restaurant_id") if result and result.get("found") else None

    if not restaurant_id:
        print("\n" + "!"*60)
        print("WARNING: No restaurant found. Please ensure:")
        print("  1. You have a restaurant in the database")
        print("  2. The restaurant has a twilio_phone_number set")
        print("  3. Update the phone number in this test script")
        print("!"*60)

        # Try with restaurant_id = 1 as fallback
        print("\nTrying with restaurant_id = 1 as fallback...")
        restaurant_id = 1

    print(f"\nUsing restaurant_id: {restaurant_id}")

    # Test 2: Get restaurant info
    test_get_restaurant_info(restaurant_id)

    # Test 3: Check hours
    test_check_hours(restaurant_id)

    # Test 4: Get menu
    menu_result = test_get_menu(restaurant_id)

    # Test 5: Check specific item
    if menu_result and menu_result.get("items"):
        first_item = menu_result["items"][0]["name"]
        test_check_item(restaurant_id, first_item)
    else:
        test_check_item(restaurant_id, "chicken")  # Try common item

    # Test 6: Create order (only if menu has items)
    if menu_result and menu_result.get("items"):
        print("\n" + "-"*60)
        print("OPTIONAL: Test Create Order")
        print("This will create a real order in the database.")
        print("-"*60)
        confirm = input("Create test order? (y/n): ").strip().lower()
        if confirm == 'y':
            test_create_order(restaurant_id)

    print("\n" + "="*60)
    print("  TESTS COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
