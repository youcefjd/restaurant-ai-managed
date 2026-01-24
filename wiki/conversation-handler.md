# Conversation Handler

The core AI logic for processing customer conversations.

**File:** `backend/services/conversation_handler.py`

## Overview

The conversation handler is the brain of the voice AI system. It:
1. Loads restaurant-specific context
2. Builds a dynamic system prompt
3. Calls the LLM (Gemini or OpenAI)
4. Parses the AI response
5. Creates orders/bookings when appropriate

## Flow

```
Customer Message
      │
      ▼
Load Restaurant Context
      │
      ├── Menu (items, prices, availability)
      ├── Operating hours
      ├── Table availability
      └── Current conversation state
      │
      ▼
Build System Prompt
      │
      ├── Template from VOICE_AGENT_SYSTEM_PROMPT.md
      ├── Restaurant name, hours
      ├── Full menu data
      └── Current date/time
      │
      ▼
Call LLM (Gemini/OpenAI)
      │
      ▼
Parse Response
      │
      ├── Extract JSON from response
      ├── Intent (place_order, confirm_order, etc.)
      ├── Message to speak
      ├── Order items
      ├── Customer name
      └── Pickup time
      │
      ▼
Process Intent
      │
      ├── confirm_order → Create order in database
      ├── book_table → Create booking in database
      └── Other → Return response only
      │
      ▼
Return Structured Response
```

## Key Function

```python
async def process_message(
    message: str,
    customer_phone: str,
    restaurant_phone: str,
    conversation_history: List[Dict],
    db: SupabaseDB
) -> Dict:
    """
    Process a customer message and return AI response.

    Returns:
        {
            "intent": "place_order|confirm_order|menu_question|...",
            "message": "AI response to speak",
            "customer_name": "John",
            "order_items": [...],
            "time": "6:00 PM",
            "order_id": 123  # If order was created
        }
    """
```

## Context Loading

### Restaurant Lookup

```python
# Find restaurant by phone number
restaurant = db.query_one(
    "restaurant_accounts",
    {"twilio_phone_number": restaurant_phone}
)
```

### Menu Loading

```python
# Load full menu structure
menus = db.query_all("menus", {"account_id": account_id})
for menu in menus:
    categories = db.query_all("menu_categories", {"menu_id": menu["id"]})
    for category in categories:
        items = db.query_all(
            "menu_items",
            {"category_id": category["id"], "is_available": True}
        )
```

## System Prompt

The system prompt template is in `VOICE_AGENT_SYSTEM_PROMPT.md`.

Dynamic variables:
- `{{restaurant_name}}` - Business name
- `{{opening_time}}` - Opening time
- `{{closing_time}}` - Closing time
- `{{operating_days}}` - Days of week
- `{{current_datetime}}` - Current date/time
- `{{menu_data}}` - Full menu formatted for AI
- `{{context}}` - Current conversation state

## Response Parsing

AI responses are expected as JSON:

```json
{
  "intent": "place_order",
  "message": "Got it, one kung pao chicken. Anything else?",
  "order_items": [
    {
      "item_name": "Kung Pao Chicken",
      "quantity": 1,
      "price_cents": 1499,
      "action": "add"
    }
  ],
  "customer_name": "",
  "time": ""
}
```

## Intents

| Intent | Description |
|--------|-------------|
| `place_order` | Adding items to order |
| `confirm_order` | Customer confirming order (triggers order creation) |
| `menu_question` | Questions about menu/prices |
| `operating_hours` | Hours questions |
| `book_table` | Making reservation |
| `need_more_info` | Need clarification |
| `goodbye` | Customer ending call |
| `out_of_scope` | Request outside capabilities |
| `end_call_abuse` | Ending due to abuse |

## Order Creation

When `intent == "confirm_order"` and required info is present:

```python
if intent == "confirm_order" and customer_name and order_items:
    order = db.insert("orders", {
        "account_id": account_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "order_items": json.dumps(order_items),
        "order_type": "TAKEOUT",
        "status": "PENDING",
        "total": calculate_total(order_items),
        "pickup_time": time,
        "conversation_id": conversation_id
    })
    response["order_id"] = order["id"]
```

## Conversation State

State is tracked across messages:
- Current order items
- Customer name
- Requested pickup time
- Suggestions made

State is maintained in the WebSocket connection for voice calls, or in database for SMS.

## Error Handling

- If LLM fails: Return graceful error message
- If parsing fails: Extract message from raw text
- If database fails: Log error, return apology

---

**Related:**
- [Voice AI](./voice-ai.md)
- [Voice Agent Prompt](./voice-agent-prompt.md)
- [Services](./services.md)
