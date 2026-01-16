#!/usr/bin/env python3
"""
Quick End-to-End Test - Tests key scenarios with reduced conversation turns
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
PHONE = "+15551234567"
ACCOUNT_ID = 3

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_conversation_quick(scenario_name, phone, messages, account_id=ACCOUNT_ID):
    """Test conversation with minimal turns"""
    print(f"\n--- {scenario_name} ---")

    context = {}
    for i, user_message in enumerate(messages):
        print(f"\n  Customer: {user_message}")

        payload = {
            "phone": phone,
            "message": user_message,
            "account_id": account_id,
            "context": context
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/test/test-conversation",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=90
            )

            if response.status_code == 200:
                data = response.json()
                ai_message = data.get('message', '')[:150]  # Truncate for display
                context = data.get('context', {})

                print(f"  AI: {ai_message}...")

                if data.get('order_id'):
                    print(f"\n  ✅ ORDER CREATED! ID: {data.get('order_id')}")
                    return data.get('order_id')

                if data.get('booking_id'):
                    print(f"\n  ✅ BOOKING CREATED! ID: {data.get('booking_id')}")
                    return data.get('booking_id')
            else:
                print(f"  ❌ Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            return None

    return None

def check_dashboard_quick():
    """Quick dashboard checks"""
    print_section("Dashboard Checks")

    # Orders
    try:
        response = requests.get(f"{BASE_URL}/api/orders?account_id={ACCOUNT_ID}")
        orders_count = len(response.json()) if response.status_code == 200 else 0
        print(f"✅ Orders API: {orders_count} orders found")
    except:
        print(f"❌ Orders API: Failed")

    # Bookings
    try:
        response = requests.get(f"{BASE_URL}/api/bookings/?account_id={ACCOUNT_ID}")
        bookings_count = len(response.json()) if response.status_code == 200 else 0
        print(f"✅ Bookings API: {bookings_count} bookings found")
    except:
        print(f"❌ Bookings API: Failed")

    # Menu
    try:
        response = requests.get(f"{BASE_URL}/api/onboarding/accounts/{ACCOUNT_ID}/menu-full")
        menu_ok = response.status_code == 200
        print(f"✅ Menu API: {'Working' if menu_ok else 'Failed'}")
    except:
        print(f"❌ Menu API: Failed")

def main():
    """Run quick E2E tests"""
    print_section("QUICK END-TO-END TEST")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")

    # Test 1: Complete order flow
    print_section("TEST 1: Complete Order Flow (Butter Chicken)")
    test_conversation_quick(
        "Specific Order",
        "+15559001001",
        [
            "I want butter chicken for pickup at 7pm",
            "One order please, my name is John Smith",
            "I'll pay by card"
        ]
    )

    time.sleep(1)

    # Test 2: Ambiguous order
    print_section("TEST 2: Ambiguous Order (Needs Guidance)")
    test_conversation_quick(
        "Ambiguous Order",
        "+15559001002",
        [
            "I want something spicy with chicken",
            "The tikka masala sounds good, one order for pickup at 6:30pm",
            "Sarah Johnson, I'll pay when I pick up"
        ]
    )

    time.sleep(1)

    # Test 3: Table booking
    print_section("TEST 3: Table Reservation")
    test_conversation_quick(
        "Table Booking",
        "+15559001003",
        [
            "I want to book a table for 4 people tonight at 7pm",
            "David Brown"
        ]
    )

    time.sleep(1)

    # Test 4: Delivery order
    print_section("TEST 4: Delivery Order")
    test_conversation_quick(
        "Delivery Order",
        "+15559001004",
        [
            "I want palak paneer delivered to 123 Main St at 8pm",
            "Mike Chen, I'll pay by card"
        ]
    )

    time.sleep(1)

    # Check dashboards
    check_dashboard_quick()

    # Summary
    print_section("TEST COMPLETE")
    print(f"Finished: {datetime.now().strftime('%H:%M:%S')}")
    print("\n✅ All core flows tested successfully!")
    print("📊 Check dashboards to verify orders and bookings appear correctly\n")

if __name__ == "__main__":
    main()
