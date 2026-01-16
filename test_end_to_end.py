#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Restaurant AI Voice Assistant
Tests: Specific orders, ambiguous orders, recommendations, takeout, delivery, table bookings
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
PHONE = "+15551234567"
ACCOUNT_ID = 3

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_conversation(scenario_name, phone, messages, account_id=ACCOUNT_ID):
    """Test a complete conversation flow"""
    print(f"\n--- Testing: {scenario_name} ---\n")

    context = {}

    for i, user_message in enumerate(messages):
        print(f"Customer ({i+1}): {user_message}")

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
                ai_message = data.get('message', 'No message')
                intent = data.get('intent', 'unknown')
                context = data.get('context', {})

                print(f"AI Response: {ai_message}")
                print(f"Intent: {intent}")
                print(f"Context: {json.dumps(context, indent=2)}")

                # Check if order was created
                if data.get('order_id'):
                    print(f"✅ Order created! Order ID: {data.get('order_id')}")
                    return data.get('order_id')

                # Check if booking was created
                if data.get('booking_id'):
                    print(f"✅ Booking created! Booking ID: {data.get('booking_id')}")
                    return data.get('booking_id')

            else:
                print(f"❌ Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")

        time.sleep(1)

    return None

def check_orders_dashboard():
    """Check orders in dashboard"""
    print_section("Checking Orders Dashboard")

    try:
        response = requests.get(f"{BASE_URL}/api/orders?account_id={ACCOUNT_ID}")
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ Found {len(orders)} orders in dashboard")

            for order in orders[:5]:  # Show latest 5
                print(f"\nOrder #{order['id']}:")
                print(f"  Customer: {order.get('customer_name')} - {order.get('customer_phone')}")
                print(f"  Status: {order['status']}")
                print(f"  Total: ${order['total']/100:.2f}")
                print(f"  Payment: {order.get('payment_method')} - {order.get('payment_status')}")
                print(f"  Delivery: {order['delivery_address']}")

                # Parse order items
                try:
                    items = json.loads(order['order_items']) if isinstance(order['order_items'], str) else order['order_items']
                    print(f"  Items:")
                    for item in items:
                        print(f"    - {item.get('quantity', 1)}x {item.get('item_name')} ${item.get('price_cents', 0)/100:.2f}")
                except:
                    print(f"  Items: {order['order_items']}")

            return True
        else:
            print(f"❌ Failed to get orders: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def check_bookings_dashboard():
    """Check bookings in dashboard"""
    print_section("Checking Bookings Dashboard")

    try:
        response = requests.get(f"{BASE_URL}/api/bookings/?account_id={ACCOUNT_ID}")
        if response.status_code == 200:
            bookings = response.json()
            print(f"✅ Found {len(bookings)} bookings in dashboard")

            for booking in bookings[:5]:  # Show latest 5
                print(f"\nBooking #{booking['id']}:")
                print(f"  Date: {booking['booking_date']} at {booking['booking_time']}")
                print(f"  Party size: {booking['party_size']} guests")
                print(f"  Table: #{booking.get('table_id')}")
                print(f"  Status: {booking['status']}")
                print(f"  Customer: {booking.get('customer', {}).get('name')} - {booking.get('customer', {}).get('phone')}")

            return True
        else:
            print(f"❌ Failed to get bookings: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_api_endpoints():
    """Test all API endpoints"""
    print_section("Testing API Endpoints")

    endpoints = [
        ("GET", f"/api/orders?account_id={ACCOUNT_ID}", "Orders API"),
        ("GET", f"/api/bookings/?account_id={ACCOUNT_ID}", "Bookings API"),
        ("GET", f"/api/onboarding/accounts/{ACCOUNT_ID}/menu-full", "Menu API"),
    ]

    results = []

    for method, endpoint, name in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}")

            if response.status_code in [200, 201]:
                print(f"✅ {name}: SUCCESS ({response.status_code})")
                results.append(True)
            else:
                print(f"❌ {name}: FAILED ({response.status_code}) - {response.text[:100]}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: EXCEPTION - {str(e)}")
            results.append(False)

    return all(results)

def main():
    """Run all end-to-end tests"""
    print_section("RESTAURANT AI VOICE ASSISTANT - COMPREHENSIVE E2E TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: Specific order (customer knows exactly what they want)
    print_section("TEST 1: Specific Order - Butter Chicken Takeout")
    test_conversation(
        "Specific Order",
        PHONE,
        [
            "I'd like to order butter chicken for takeout",
            "Yes, one order please",
            "Pickup at 7pm tonight",
            "John Smith",
            "Pay with card"
        ]
    )

    time.sleep(2)

    # Test 2: Ambiguous order (needs guidance)
    print_section("TEST 2: Ambiguous Order - Something Spicy")
    test_conversation(
        "Ambiguous Order",
        "+15559876543",
        [
            "I want something spicy for dinner",
            "I like chicken",
            "Yeah the chicken tikka masala sounds good",
            "Just one please",
            "Pickup at 6:30pm",
            "Sarah Johnson",
            "I'll pay when I pick it up"
        ]
    )

    time.sleep(2)

    # Test 3: Asking for recommendations
    print_section("TEST 3: Asking for Recommendations")
    test_conversation(
        "Recommendations",
        "+15558675309",
        [
            "What do you recommend for vegetarians?",
            "Tell me about the palak paneer",
            "How much is it?",
            "Okay I'll take one palak paneer",
            "Delivery to 123 Main Street",
            "6pm tonight",
            "Mike Chen",
            "Credit card"
        ]
    )

    time.sleep(2)

    # Test 4: Order with extras (upselling scenario)
    print_section("TEST 4: Order with Extra Meat")
    test_conversation(
        "Order with Extras",
        "+15557654321",
        [
            "I want chicken tikka masala",
            "Yes, add extra chicken please",
            "One order",
            "Pickup at 7:30pm",
            "Lisa Anderson",
            "Card payment"
        ]
    )

    time.sleep(2)

    # Test 5: Table booking
    print_section("TEST 5: Table Reservation")
    test_conversation(
        "Table Booking",
        "+15556549870",
        [
            "I'd like to book a table for tonight",
            "7pm",
            "Four people",
            "David Brown"
        ]
    )

    time.sleep(2)

    # Test 6: Delivery order with specific address
    print_section("TEST 6: Delivery Order with Address")
    test_conversation(
        "Delivery Order",
        "+15559998877",
        [
            "I want samosas and naan delivered",
            "Two orders of samosas and one garlic naan",
            "456 Oak Avenue, Apartment 3B",
            "8pm tonight",
            "Emily Davis",
            "I'll pay by card"
        ]
    )

    time.sleep(2)

    # Test 7: Multiple items order
    print_section("TEST 7: Multiple Items Order")
    test_conversation(
        "Multiple Items",
        "+15553334455",
        [
            "I want to order tikka masala and naan",
            "One chicken tikka masala and two garlic naan",
            "Pickup at 6pm",
            "Robert Wilson",
            "Card"
        ]
    )

    time.sleep(3)

    # Check dashboards
    orders_ok = check_orders_dashboard()
    time.sleep(1)
    bookings_ok = check_bookings_dashboard()
    time.sleep(1)

    # Test API endpoints
    api_ok = test_api_endpoints()

    # Summary
    print_section("TEST SUMMARY")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n✅ Orders Dashboard: {'PASS' if orders_ok else 'FAIL'}")
    print(f"✅ Bookings Dashboard: {'PASS' if bookings_ok else 'FAIL'}")
    print(f"✅ API Endpoints: {'PASS' if api_ok else 'FAIL'}")

    print("\n" + "="*80)
    print("Test complete! Check the output above for any issues.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
