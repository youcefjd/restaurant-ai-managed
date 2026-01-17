# Restaurant AI Platform - Functional Specification Index

**Purpose**: Index and overview of all functional specification documents

---

## Document Overview

This set of functional specification documents provides a complete, implementation-agnostic description of the Restaurant AI Platform. These documents focus on **what** the system does and **how** it works functionally, without specifying technical implementation details.

Another development team can use these specifications to:
- Understand all features and capabilities
- Design their own technical architecture
- Choose their own technology stack
- Recreate the platform functionality

---

## Documents in This Specification

### 1. [FUNCTIONAL_SPECIFICATION.md](./FUNCTIONAL_SPECIFICATION.md)
**Main Functional Specification**

**Contents**:
- Executive summary and business model
- User roles and capabilities (Platform Admin, Restaurant Owner, Customer)
- Core functional areas:
  - Restaurant onboarding
  - Menu management
  - Order management
  - Table reservations
  - Voice AI assistant
  - SMS/text messaging
  - Payment processing
  - Commission management
  - Analytics and reporting
- Integration requirements
- User workflows
- Success criteria

**Read this first** to understand the overall system.

---

### 2. [AI_CONVERSATION_SPECIFICATION.md](./AI_CONVERSATION_SPECIFICATION.md)
**AI Conversation System Specification**

**Contents**:
- Detailed voice call flow (phone)
- Detailed SMS/text message flow
- AI capabilities (menu questions, orders, reservations, hours)
- Conversation context management
- AI prompt engineering
- Error handling
- Restaurant-specific personalization
- Integration requirements (voice service, SMS service, AI/LLM service)

**Read this** to understand how the AI conversation system works.

---

### 3. [DATA_MODELS_AND_WORKFLOWS.md](./DATA_MODELS_AND_WORKFLOWS.md)
**Data Models and Complete Workflows**

**Contents**:
- Complete data model definitions (all entities)
- Detailed property lists for each entity
- Relationships between entities
- Business rules per entity
- Complete workflow descriptions:
  - Restaurant onboarding
  - Customer places order via phone
  - Restaurant fulfills order
  - Customer makes reservation via SMS
  - Restaurant toggles menu availability
  - Admin manages commission
  - Reservation conflict prevention

**Read this** to understand data structures and detailed business logic.

---

## How to Use These Documents

### For Project Planning

1. Read `FUNCTIONAL_SPECIFICATION.md` to understand scope
2. Review user roles and capabilities
3. Identify core features needed
4. Map features to development phases

### For Technical Design

1. Review `DATA_MODELS_AND_WORKFLOWS.md` for data structures
2. Understand entity relationships
3. Design database schema based on entities
4. Design API endpoints based on workflows

### For AI Implementation

1. Read `AI_CONVERSATION_SPECIFICATION.md` thoroughly
2. Understand conversation flows
3. Design prompt engineering approach
4. Plan context management strategy
5. Select AI/LLM service provider

### For Feature Implementation

1. Find relevant workflow in `DATA_MODELS_AND_WORKFLOWS.md`
2. Understand business rules
3. Review data models involved
4. Implement according to workflow steps
5. Verify against success criteria in `FUNCTIONAL_SPECIFICATION.md`

---

## Key Functional Areas

### 1. Multi-Tenant Restaurant Management
- **Documents**: FUNCTIONAL_SPECIFICATION.md, DATA_MODELS_AND_WORKFLOWS.md
- **Key Entities**: RestaurantAccount, Restaurant, Menu
- **Purpose**: Support multiple independent restaurants in one platform

### 2. AI-Powered Conversations
- **Documents**: AI_CONVERSATION_SPECIFICATION.md
- **Channels**: Voice calls, SMS/text messages
- **Purpose**: Automated customer service and order taking

### 3. Menu Management
- **Documents**: FUNCTIONAL_SPECIFICATION.md, DATA_MODELS_AND_WORKFLOWS.md
- **Key Entities**: Menu, MenuCategory, MenuItem, MenuModifier
- **Purpose**: Restaurants create and manage menus with real-time availability

### 4. Order Management
- **Documents**: FUNCTIONAL_SPECIFICATION.md, DATA_MODELS_AND_WORKFLOWS.md
- **Key Entities**: Order, Delivery, Customer
- **Purpose**: Handle orders from creation through completion

### 5. Table Reservations
- **Documents**: FUNCTIONAL_SPECIFICATION.md, DATA_MODELS_AND_WORKFLOWS.md
- **Key Entities**: Table, Booking, Customer
- **Purpose**: Manage table bookings with conflict prevention

### 6. Payment and Commission
- **Documents**: FUNCTIONAL_SPECIFICATION.md, DATA_MODELS_AND_WORKFLOWS.md
- **Key Feature**: Automatic commission calculation and splitting
- **Purpose**: Revenue tracking and payment processing

---

## Integration Requirements Summary

### Required Third-Party Services

1. **Voice/SMS Service** (e.g., Twilio)
   - Phone number management
   - Voice call handling
   - SMS message handling
   - Speech-to-text
   - Text-to-speech

2. **AI/LLM Service** (e.g., Google Gemini, OpenAI)
   - Natural language understanding
   - Context-aware conversation handling
   - Fast response times

3. **Payment Processing** (e.g., Stripe Connect)
   - Payment collection
   - Automatic payment splitting (commission + restaurant)
   - Payout management

### Optional Services

- **Google Maps API**: Operating hours import
- **Image Storage**: Menu item images (AWS S3, Cloudinary, etc.)
- **Analytics Service**: Usage analytics (future)

---

## Key Business Rules Summary

### Commission
- Commission is a percentage of order total (default 10%)
- Commission is invisible to customers
- Commission rate configurable per restaurant (0-100%)
- Commission can be enabled/disabled per restaurant

### Availability
- Menu items must be marked `is_available = true` to appear in AI responses
- Tables must be marked `is_active = true` to be considered for reservations
- No overlapping reservations on same table

### Orders
- Order must have at least one item
- Delivery address required if `order_type = DELIVERY`
- Order status progresses sequentially

### Reservations
- Party size must be <= table capacity
- Default reservation duration: 90 minutes
- Automatic table assignment (smallest suitable table)

### Multi-Tenancy
- Each restaurant has unique phone number
- Data isolated per restaurant (no cross-contamination)
- Menu and settings specific per restaurant

---

## Success Criteria

A successful implementation must:

1. ✅ Support multiple restaurants independently (multi-tenant)
2. ✅ Enable restaurants to create and manage menus
3. ✅ Handle AI phone and SMS conversations
4. ✅ Process orders from creation to completion
5. ✅ Manage table reservations with conflict prevention
6. ✅ Process payments with automatic commission splitting
7. ✅ Provide dashboards for restaurants and admin
8. ✅ Track commission automatically
9. ✅ Support real-time menu availability updates
10. ✅ Maintain conversation context during AI interactions

---

## Out of Scope (Future Enhancements)

These features are NOT in the current specification but may be added later:

- Customer-facing web ordering interface
- Mobile apps (iOS/Android)
- Inventory management
- Staff scheduling
- Loyalty programs
- Marketing campaigns
- Advanced analytics (predictive, ML-based)
- Multi-language support
- QR code ordering
- In-store kiosk ordering
- Delivery driver tracking app
- Advanced reporting with exports

---

## Document Version History

- **Version 1.0** (January 2026): Initial complete functional specification

---

## Questions and Clarifications

When implementing based on these specifications:

1. **Technical Choices**: Choose your own stack (database, framework, deployment)
2. **Architecture**: Design architecture appropriate for your scale
3. **UI/UX**: Design interfaces as needed (specifications don't prescribe UI)
4. **Non-Functional Requirements**: Implement performance, security, scalability as needed

**Focus**: These specifications define **functionality**, not **implementation**.

---

## Quick Reference

| Document | When to Read |
|----------|--------------|
| **FUNCTIONAL_SPECIFICATION.md** | Start here - overall system understanding |
| **AI_CONVERSATION_SPECIFICATION.md** | Implementing AI/voice/SMS features |
| **DATA_MODELS_AND_WORKFLOWS.md** | Designing database and implementing workflows |

---

**End of Specification Index**
