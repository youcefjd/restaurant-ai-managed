# AI Conversation System - Functional Specification

**Purpose**: Detailed specification for the AI-powered conversation system that handles phone calls and SMS messages

---

## Overview

The AI Conversation System enables restaurants to have automated phone answering and text messaging. Customers can call or text a restaurant's phone number and have a natural conversation with an AI assistant that understands the restaurant's specific menu, can take orders, make reservations, and answer questions.

---

## Key Characteristics

### 1. Multi-Tenant Support
- Each restaurant has its own phone number
- AI responses are specific to that restaurant's menu and settings
- No cross-contamination between restaurants

### 2. Context Awareness
- AI knows the restaurant's menu (items, prices, dietary tags)
- AI knows operating hours and days
- AI knows available tables for reservations
- AI maintains conversation context during interaction

### 3. Natural Language Understanding
- Handles variations: "tonight" = today, "7pm" = 19:00
- Understands menu questions: "What vegetarian options do you have?"
- Processes complex orders: "2 pizzas, extra cheese, no onions"
- Makes reservations: "Table for 4 tomorrow at 7pm"

---

## Voice Call Flow (Phone)

### Call Initiation

1. **Customer calls restaurant phone number**
   - Example: Customer dials +15551234567
   - Twilio receives call
   - Twilio sends webhook to platform: `POST /api/voice/welcome`

2. **System identifies restaurant**
   - Uses phone number ("To" parameter) to lookup restaurant
   - Finds RestaurantAccount where `twilio_phone_number` matches
   - Loads restaurant's menu, hours, and settings

3. **AI generates greeting**
   - Personalizes greeting: "Thanks for calling [Restaurant Name]"
   - Uses restaurant-specific information
   - Returns TwiML for Twilio to play greeting

### Conversation Processing

4. **Customer speaks**
   - Customer: "I want to order a pizza"
   - Twilio converts speech to text using speech-to-text service
   - Twilio sends webhook: `POST /api/voice/process` with text

5. **AI processes request**
   - System receives customer text: "I want to order a pizza"
   - System loads restaurant's menu context
   - Sends to AI/LLM with prompt:
     - Restaurant name
     - Full menu (items, prices, dietary tags)
     - Operating hours
     - Conversation context
   - AI generates response based on menu

6. **AI responds**
   - AI: "Great! We have Margherita Pizza ($15), Pepperoni Pizza ($17), Veggie Pizza ($16). Which would you like?"
   - System converts text to speech
   - Twilio plays response to customer

7. **Conversation continues**
   - Repeat steps 4-6 until order/booking complete
   - Maintain context throughout conversation
   - Handle clarifications and modifications

### Order/Reservation Completion

8. **Order confirmed**
   - Customer confirms order details
   - AI: "Perfect! Your order is confirmed. Order #1234. Total: $34. We'll have it ready in 30 minutes."
   - System creates Order in database
   - System sends SMS confirmation to customer

9. **Reservation confirmed**
   - Customer confirms reservation details
   - AI: "Table reserved for 4 guests tonight at 7pm. Confirmation #5678."
   - System creates Booking in database
   - System sends SMS confirmation to customer

10. **Call ends**
    - AI: "Is there anything else I can help you with?"
    - If no: "Thanks for calling! Have a great day!"
    - Twilio ends call

---

## SMS/Text Message Flow

### Message Initiation

1. **Customer texts restaurant phone number**
   - Example: Customer texts +15551234567: "Hi, can I order a pizza?"
   - Twilio receives SMS
   - Twilio sends webhook: `POST /api/voice/sms/incoming`

2. **System identifies restaurant**
   - Uses phone number ("To" parameter) to lookup restaurant
   - Finds RestaurantAccount where `twilio_phone_number` matches
   - Loads restaurant's menu context

### Conversation Processing

3. **AI processes message**
   - System receives customer text: "Hi, can I order a pizza?"
   - System loads conversation state (if exists)
   - Sends to AI/LLM with menu context
   - AI generates response

4. **AI responds via SMS**
   - AI: "Sure! We have Margherita ($15), Pepperoni ($17), Veggie ($16). Which would you like?"
   - System sends TwiML SMS response to Twilio
   - Twilio delivers SMS to customer

5. **Conversation continues asynchronously**
   - Customer can respond minutes or hours later
   - System maintains conversation state
   - Context preserved across messages
   - No time limit (unlike phone calls)

### Order/Reservation Completion

6. **Order confirmed**
   - Customer confirms via text
   - AI: "✅ Order #1234 confirmed! Total: $34. We'll text when it's ready!"
   - System creates Order in database
   - Order appears in restaurant dashboard

7. **Reservation confirmed**
   - Customer confirms via text
   - AI: "✅ Table reserved! 4 guests, tonight 7pm. Confirmation #5678"
   - System creates Booking in database
   - Reservation appears in restaurant dashboard

---

## AI Capabilities

### 1. Menu Questions

**Customer**: "What vegetarian options do you have?"  
**AI Response**: Lists all items with "vegetarian" dietary tag, including prices and descriptions.

**Example**:
```
"We have several delicious vegetarian options:
- Palak Paneer ($13.99) - Cottage cheese in spinach sauce
- Chana Masala ($11.99) - Chickpeas in spicy gravy
- Vegetable Biryani ($12.99) - Mixed vegetables with rice
Would you like to order any of these?"
```

**Functional Requirements**:
- Filter menu items by dietary tags
- Include prices in responses
- Provide descriptions
- Only show available items

### 2. Price Queries

**Customer**: "How much is the shawarma?"  
**AI Response**: Provides exact price for the item.

**Example**:
```
"The Chicken Shawarma Wrap is $12.00. Would you like to order it?"
```

**Functional Requirements**:
- Exact price matching
- Handle variations: "shawarma" vs "Chicken Shawarma Wrap"
- Include currency formatting

### 3. Order Taking

**Customer**: "I want 2 pizzas, extra cheese, no onions"  
**AI Response**: Processes order with modifiers and calculates total.

**Functional Requirements**:
- Extract quantities (2 pizzas)
- Extract modifiers (extra cheese, no onions)
- Match items to menu (handle variations)
- Calculate total price including modifiers
- Confirm order details before finalizing

**Example Conversation**:
```
Customer: "I want 2 large pepperoni pizzas, extra cheese"
AI: "Got it! 2 large pepperoni pizzas with extra cheese. 
     That's $34.00 (2 × $17.00). Delivery or pickup?"
Customer: "Delivery to 123 Main St"
AI: "Perfect! Total is $34.00. Estimated delivery: 30 minutes. 
     Confirm order?"
Customer: "Yes"
AI: "✅ Order #1234 confirmed! We'll text when it's on the way!"
```

### 4. Reservations

**Customer**: "Can I book a table for 4 tomorrow at 7pm?"  
**AI Response**: Checks availability, creates booking if available.

**Functional Requirements**:
- Parse date/time: "tomorrow", "7pm", "tonight"
- Check table availability for party size
- Suggest alternative times if unavailable
- Collect customer name
- Create booking in database
- Confirm reservation details

**Example Conversation**:
```
Customer: "Table for 4 tonight at 7pm"
AI: [Checks availability]
    "Great! I have a table for 4 available at 7pm tonight. 
     What name should I put it under?"
Customer: "Sarah Johnson"
AI: "Perfect! Table reserved for 4 guests tonight at 7pm. 
     Name: Sarah Johnson. Confirmation #5678"
```

**If Unavailable**:
```
Customer: "Table for 6 tonight at 7pm"
AI: [Checks availability]
    "I don't have a table for 6 available at 7pm tonight. 
     However, I have availability at 6pm, 8pm, or 9pm. 
     Would any of those work?"
Customer: "8pm is fine"
AI: [Checks 8pm]
    "Perfect! Table reserved for 6 guests tonight at 8pm..."
```

### 5. Operating Hours

**Customer**: "What time do you close?"  
**AI Response**: Provides operating hours.

**Example**:
```
"We're open from 11:00 AM to 10:00 PM, Monday through Sunday. 
 Is there anything else I can help you with?"
```

**Functional Requirements**:
- Use restaurant's configured hours
- Handle "closed" responses if outside hours
- Format times in readable format

---

## Conversation Context Management

### Context Elements

1. **Restaurant Context** (permanent)
   - Restaurant name
   - Menu items and prices
   - Operating hours
   - Table availability

2. **Conversation Context** (session-based)
   - Current order items (if building order)
   - Current reservation details (if making booking)
   - Previous messages in conversation
   - Customer name (if provided)

### Context Preservation

**Voice Calls**:
- Context maintained during call duration
- Lost when call ends
- Stored in memory (can use Redis for production)

**SMS Messages**:
- Context maintained across messages
- Can span hours or days
- Stored with unique key: `{customer_phone}_{restaurant_phone}`
- Expires after 24 hours of inactivity (configurable)

### Example: Multi-Turn Order

```
Turn 1:
Customer: "I want a pizza"
AI: "Which pizza would you like? We have..."

Turn 2:
Customer: "Pepperoni, large"
AI: "Large pepperoni pizza. Would you like anything else?"
[Context: current order = {pepperoni pizza, large}]

Turn 3:
Customer: "And a side salad"
AI: "Got it! 1 large pepperoni pizza and 1 side salad. Total: $22.00. Delivery or pickup?"
[Context: current order = {pepperoni pizza large, side salad}]

Turn 4:
Customer: "Pickup"
AI: "Perfect! Order confirmed. Order #1234. Ready in 30 minutes."
[Context: Order created, conversation can end]
```

---

## AI Prompt Engineering

### System Prompt Structure

The AI receives a system prompt that includes:

```
You are an AI assistant for [Restaurant Name].

RESTAURANT INFORMATION:
- Name: [Business Name]
- Hours: [Opening Time] - [Closing Time]
- Days: [Operating Days]

MENU:
[Full menu with categories, items, prices, dietary tags, modifiers]

CAPABILITIES:
- Answer menu questions
- Take orders (takeout, delivery)
- Make table reservations
- Provide operating hours

INSTRUCTIONS:
- Only offer items marked as "available"
- Provide accurate prices
- For orders: collect type (takeout/delivery), address if delivery, confirm total
- For reservations: check availability, collect party size, date, time, name
- Be friendly and conversational
- If unsure, ask for clarification
```

### Context Injection

Each conversation turn includes:
- Customer's current message
- Conversation history (last N messages)
- Current order/reservation state (if building)
- Restaurant context (menu, hours, tables)

---

## Error Handling

### Unclear Requests

**Customer**: "I want food"  
**AI Response**: "I'd be happy to help! What would you like to order? We have [categories]. Which interests you?"

### Item Not Found

**Customer**: "I want a hamburger"  
**AI Response** (if no hamburger on menu): "We don't have hamburgers on our menu. We have [similar items]. Would you like to try one of these instead?"

### Availability Issues

**Customer**: "I want the grilled salmon"  
**AI Response** (if unavailable): "Sorry, we're currently out of grilled salmon. Would you like to try [alternative] instead?"

### Unavailable Time

**Customer**: "Table for 4 tonight at 11pm"  
**AI Response**: "We close at 10pm, so we can't take reservations for 11pm. Would 8pm or 9pm work?"

---

## Restaurant-Specific Personalization

### Dynamic Menu Loading

- Each conversation loads only that restaurant's menu
- Menu includes current availability status
- Unavailable items are filtered out from AI context

### Personalized Greetings

- Uses restaurant's actual business name
- Can include special messages or promotions (future)

### Operating Hours

- AI responds with restaurant's configured hours
- Can handle different hours on different days (future)

---

## Integration Requirements

### Voice Service (Twilio or equivalent)

**Required Capabilities**:
- Incoming call webhooks
- Speech-to-text (real-time or post-call)
- Text-to-speech (TTS) for responses
- Call status callbacks
- Phone number management

**Webhook Endpoints**:
- `POST /api/voice/welcome` - Initial call greeting
- `POST /api/voice/process` - Process customer speech
- `POST /api/voice/status` - Call status updates

### SMS Service (Twilio or equivalent)

**Required Capabilities**:
- Incoming SMS webhooks
- Outgoing SMS delivery
- Phone number management

**Webhook Endpoints**:
- `POST /api/voice/sms/incoming` - Process incoming SMS
- `POST /api/voice/sms/health` - Health check

### AI/LLM Service (Google Gemini, OpenAI, or equivalent)

**Required Capabilities**:
- Natural language understanding
- Context-aware responses
- Function calling (optional, for structured data extraction)
- Fast response times (< 5 seconds)

**API Usage**:
- Send prompt with restaurant context + conversation history
- Receive AI-generated response
- Handle rate limits and errors

---

## Data Requirements

### Menu Data (for AI Context)

Each restaurant's menu must be available in a structured format:
```json
{
  "restaurant_name": "Mediterranean Delights",
  "hours": "11:00 - 22:00",
  "menu": [
    {
      "category": "Main Dishes",
      "items": [
        {
          "name": "Chicken Shawarma Wrap",
          "price": 12.00,
          "description": "Marinated chicken with vegetables",
          "dietary_tags": ["halal"],
          "is_available": true,
          "modifiers": [
            {"name": "Extra sauce", "price_adjustment": 0.50},
            {"name": "No onions", "price_adjustment": 0}
          ]
        }
      ]
    }
  ]
}
```

### Conversation State (Session Data)

Store per conversation:
- Customer phone number
- Restaurant phone number
- Conversation history (messages)
- Current order state (if building order)
- Current reservation state (if making booking)
- Timestamp of last interaction

---

## Success Criteria

A successful AI conversation system must:

1. ✅ Identify restaurant correctly by phone number
2. ✅ Load restaurant-specific menu and context
3. ✅ Handle menu questions accurately
4. ✅ Process orders with modifiers correctly
5. ✅ Make reservations with availability checking
6. ✅ Maintain conversation context
7. ✅ Handle errors gracefully
8. ✅ Create orders/reservations in database
9. ✅ Send confirmations via SMS
10. ✅ Support both voice and SMS channels

---

## Future Enhancements (Out of Scope)

These features may be added later:

- Multi-language support
- Voice personality customization per restaurant
- Advanced order modifications (sizes, quantities in one phrase)
- Payment collection during conversation
- Loyalty program integration
- Upselling and recommendations
- Sentiment analysis
- Conversation analytics

---

**End of AI Conversation Specification**
