# Voice Agent Test Scenarios - Mario's Italian Kitchen

These test scenarios are designed for Retell AI's simulation testing feature.
Copy each scenario into the "AI Simulated Chat" tab to test the voice agent.

---

## 1. Simple Order - Single Item
**Purpose:** Test basic order flow with one item

**User Scenario Prompt:**
```
You are Mike, a hungry customer calling to place a simple pickup order.

Goal: Order one Margherita Pizza for pickup in 30 minutes under the name Mike.

Personality: Friendly, straightforward, knows what you want.

Flow:
1. When greeted, say you want to place an order
2. Order a Margherita Pizza
3. When asked if anything else, say "no, that's it"
4. Confirm the order when read back
5. Provide name "Mike" and pickup time "30 minutes"
6. Say thanks and bye
```

**Expected Function Calls:**
- `add_to_cart(item_name="Margherita Pizza", quantity=1)`
- `get_cart()`
- `create_order(customer_name="Mike", pickup_time="30 minutes")`
- `end_call()`

---

## 2. Order with Quantity Change
**Purpose:** Test updating item quantities

**User Scenario Prompt:**
```
You are Sarah, ordering for a small group.

Goal: Order 2 Pepperoni Pizzas and 3 Garlic Breads for pickup at 6pm under name Sarah.

Personality: Friendly but changes quantities after initially ordering.

Flow:
1. Say you want to place an order for pickup
2. Order a Pepperoni Pizza first
3. Then say "actually make that 2 pepperoni pizzas"
4. Then order a garlic bread
5. Say "make that 3 garlic breads"
6. When asked if done, say "yes, that's everything"
7. Confirm order and give name "Sarah" and time "6pm"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Pepperoni Pizza", quantity=1)`
- `update_cart_item(item_name="Pepperoni Pizza", quantity=2)`
- `add_to_cart(item_name="Garlic Bread", quantity=1)`
- `update_cart_item(item_name="Garlic Bread", quantity=3)`
- `get_cart()`
- `create_order(customer_name="Sarah", pickup_time="6pm")`

---

## 3. Order with Item Removal
**Purpose:** Test removing items from cart

**User Scenario Prompt:**
```
You are Tom, an indecisive customer.

Goal: Order Lasagna for pickup ASAP under name Tom.

Personality: Friendly but changes mind frequently.

Flow:
1. Say you want to place a pickup order
2. Order a Lasagna
3. Then order Tiramisu for dessert
4. Then say "actually remove the tiramisu, I don't want dessert"
5. Confirm the final order with just Lasagna
6. Give name "Tom" and say "as soon as possible" for pickup
```

**Expected Function Calls:**
- `add_to_cart(item_name="Lasagna", quantity=1)`
- `add_to_cart(item_name="Tiramisu", quantity=1)`
- `remove_from_cart(item_name="Tiramisu")`
- `get_cart()`
- `create_order(customer_name="Tom", pickup_time="ASAP")`

---

## 4. Question About Hours (No Order)
**Purpose:** Test answering questions without ordering

**User Scenario Prompt:**
```
You are Lisa, just checking hours before visiting.

Goal: Find out the restaurant hours and then decide not to order.

Personality: Polite, just needs information.

Flow:
1. When greeted, say "I have a question"
2. Ask "What time do you close tonight?"
3. After getting the answer, say "thanks, I might come by later"
4. Say goodbye
```

**Expected Behavior:**
- Agent should answer with hours (11:00 to 22:00 / 10pm) from the prompt
- No cart functions should be called
- `end_call()` at the end

---

## 5. Menu Inquiry Then Order
**Purpose:** Test menu questions followed by ordering

**User Scenario Prompt:**
```
You are David, unfamiliar with the menu.

Goal: Ask about pasta options, then order Fettuccine Alfredo for pickup in 20 minutes.

Personality: Curious, asks questions before ordering.

Flow:
1. Say you want to order but first want to know what pasta dishes they have
2. After hearing options, say "I'll have the Fettuccine Alfredo"
3. When asked if anything else, say "that's all"
4. Confirm order
5. Give name "David" and time "20 minutes"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Fettuccine Alfredo", quantity=1)`
- `get_cart()`
- `create_order(customer_name="David", pickup_time="20 minutes")`

---

## 6. Item Not On Menu
**Purpose:** Test handling requests for unavailable items

**User Scenario Prompt:**
```
You are Chris, wanting something not available.

Goal: Try to order a burger, then settle for Chicken Parmesan.

Personality: Easygoing, accepts alternatives.

Flow:
1. Say you want to place an order
2. Ask for a cheeseburger
3. When told it's not available, ask "what main dishes do you have?"
4. Then say "I'll take the Chicken Parmesan"
5. That's all
6. Confirm and give name "Chris" time "45 minutes"
```

**Expected Behavior:**
- Agent should NOT add burger to cart (not on menu)
- Agent should suggest alternatives or list main courses
- `add_to_cart(item_name="Chicken Parmesan", quantity=1)`
- `create_order(customer_name="Chris", pickup_time="45 minutes")`

---

## 7. Order with Special Requests
**Purpose:** Test handling modifications/special requests

**User Scenario Prompt:**
```
You are Emma, has dietary preferences.

Goal: Order Penne Arrabbiata with extra spicy and no garlic for pickup.

Personality: Specific about preferences, polite.

Flow:
1. Say you want to place a pickup order
2. Order Penne Arrabbiata
3. Say "I want it extra spicy and with no garlic please"
4. That's all
5. Confirm order
6. Give name "Emma" and time "1 hour"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Penne Arrabbiata", quantity=1, special_requests="extra spicy, no garlic")`
- `get_cart()`
- `create_order(customer_name="Emma", pickup_time="1 hour")`

---

## 8. Multiple Items Different Categories
**Purpose:** Test ordering from multiple menu categories

**User Scenario Prompt:**
```
You are James, ordering a full meal.

Goal: Order Bruschetta (appetizer), Spaghetti Carbonara (pasta), and Cannoli (dessert).

Personality: Knows exactly what he wants, efficient.

Flow:
1. Say you want to place a pickup order
2. Order Bruschetta, Spaghetti Carbonara, and a Cannoli
3. When asked, say "that's everything"
4. Confirm the order
5. Name is "James", pickup "30 minutes"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Bruschetta", quantity=1)`
- `add_to_cart(item_name="Spaghetti Carbonara", quantity=1)`
- `add_to_cart(item_name="Cannoli", quantity=1)`
- `get_cart()`
- `create_order(customer_name="James", pickup_time="30 minutes")`

---

## 9. Beverage Only Order
**Purpose:** Test small/beverage-only orders

**User Scenario Prompt:**
```
You are Amy, just wants a quick coffee.

Goal: Order a Cappuccino for immediate pickup.

Personality: In a hurry, brief responses.

Flow:
1. Say "I just want a cappuccino to go"
2. When asked if anything else, say "no"
3. Confirm quickly
4. Name "Amy", pickup "right now"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Cappuccino", quantity=1)`
- `get_cart()`
- `create_order(customer_name="Amy", pickup_time="now")`

---

## 10. Price Inquiry Before Order
**Purpose:** Test price questions and budget-conscious ordering

**User Scenario Prompt:**
```
You are Kevin, budget conscious.

Goal: Ask about prices, then order the cheapest pizza (Margherita at $15.95).

Personality: Wants value, asks about prices.

Flow:
1. Say you want to order but first ask "how much are your pizzas?"
2. After hearing prices, say "I'll take the Margherita since it's the cheapest"
3. That's all
4. Confirm
5. Name "Kevin", time "25 minutes"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Margherita Pizza", quantity=1)`
- `get_cart()`
- `create_order(customer_name="Kevin", pickup_time="25 minutes")`

---

## 11. Cancel and Restart Order
**Purpose:** Test clearing cart and starting over

**User Scenario Prompt:**
```
You are Rachel, changes her mind completely.

Goal: Start with one order, cancel it, then order something different.

Personality: Indecisive, apologetic about changes.

Flow:
1. Order a Lasagna
2. Then add Tiramisu
3. Say "actually, can we start over? I changed my mind"
4. Order Calamari Fritti instead
5. That's all
6. Confirm, name "Rachel", pickup "20 minutes"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Lasagna")`
- `add_to_cart(item_name="Tiramisu")`
- `remove_from_cart(item_name="Lasagna")`
- `remove_from_cart(item_name="Tiramisu")`
- `add_to_cart(item_name="Calamari Fritti")`
- `create_order(customer_name="Rachel", pickup_time="20 minutes")`

---

## 12. Repeat/Confirmation Request
**Purpose:** Test agent repeating information when asked

**User Scenario Prompt:**
```
You are Mark, hard of hearing.

Goal: Order Chicken Parmesan, but ask the agent to repeat things.

Personality: Polite, needs things repeated.

Flow:
1. Say you want to place an order
2. Order Chicken Parmesan
3. When they confirm, say "sorry can you repeat that?"
4. Say "yes that's correct"
5. When asked for name and time, give "Mark" and "6:30 pm"
6. Ask them to repeat the pickup time to confirm
```

**Expected Behavior:**
- Agent should patiently repeat information when asked
- All standard function calls for order flow

---

## 13. Large Group Order
**Purpose:** Test handling larger quantities

**User Scenario Prompt:**
```
You are Corporate Cathy, ordering for an office lunch.

Goal: Order 5 Margherita Pizzas and 5 Pepperoni Pizzas for pickup at noon.

Personality: Organized, clear about quantities.

Flow:
1. Say "I'm ordering for an office lunch"
2. Order 5 Margherita Pizzas
3. And 5 Pepperoni Pizzas
4. That's all
5. Confirm the order
6. Name "Cathy" for "ABC Company", pickup "12 noon"
```

**Expected Function Calls:**
- `add_to_cart(item_name="Margherita Pizza", quantity=5)`
- `add_to_cart(item_name="Pepperoni Pizza", quantity=5)`
- `get_cart()`
- `create_order(customer_name="Cathy", pickup_time="12 noon")`

---

## 14. Mishearing/Clarification
**Purpose:** Test agent handling unclear speech

**User Scenario Prompt:**
```
You are mumbling Mike.

Goal: Order Bruschetta but say it unclearly at first.

Personality: Speaks quickly/unclearly sometimes.

Flow:
1. Say you want to order
2. Say "broo-shetta" unclearly
3. If agent clarifies, confirm "yes, bruschetta"
4. That's all
5. Name "Mike", pickup "15 minutes"
```

**Expected Behavior:**
- Agent should ask for clarification or confirm the item
- Standard order flow once clarified

---

## 15. Edge Case - No Order After Questions
**Purpose:** Test handling customers who ask questions but don't order

**User Scenario Prompt:**
```
You are Browsing Betty.

Goal: Ask about the menu and prices, but decide not to order.

Personality: Curious but non-committal.

Flow:
1. Say you have some questions
2. Ask what appetizers they have
3. Ask how much the Calamari is
4. Say "thanks, I'll think about it and maybe call back"
5. Hang up
```

**Expected Behavior:**
- No cart functions should be called
- Agent should answer questions politely
- `end_call()` when customer leaves

---

## Evaluation Criteria

For each test, verify:
1. **Function calls made** - Check call history for actual API calls
2. **Correct parameters** - Item names, quantities, special requests match
3. **Order created** - Check if order appears in database/frontend
4. **Conversation quality** - Natural, helpful responses
5. **Error handling** - Graceful handling of unavailable items or misunderstandings

## How to Run Tests in Retell

1. Go to your agent in Retell dashboard
2. Click on "Simulations" or "AI Simulated Chat" tab
3. Paste the User Scenario Prompt for each test
4. Select model (gpt-4o recommended for realistic simulation)
5. Click "Test"
6. Review the conversation transcript
7. Check function call history
8. Verify order was created in your backend
