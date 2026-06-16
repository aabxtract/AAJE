# AAJE MVP REBUILD DOCUMENT

## PURPOSE

We are rebuilding AAJE cleanly.

Archive old assumptions.

Remove old hackathon complexity.

Focus on solving operational chaos for Nigerian businesses already selling online.

AAJE is a B2B SaaS operational platform.

Target businesses:

- Instagram businesses
- WhatsApp businesses
- TikTok businesses
- Facebook sellers
- Businesses already selling online
- Businesses already processing orders
- Businesses already experiencing operational stress

We are NOT building:

- another Shopify
- another banking app
- another marketplace
- offline-to-online digitization
- a super app
- autonomous AI storefront generation

Core principle:

> Businesses already know how to sell.
>
> AAJE helps them operate better.

---

# PRODUCT DIRECTION

Businesses already operate with:

WhatsApp

Instagram

Bank apps

Payment screenshots

Manual tracking

Memory

Scattered systems

AAJE centralizes operations.

Core operational layers:

1. Orders
2. Products
3. Inventory
4. Customers
5. Notifications
6. Dashboard
7. AI assistance

---

# REMOVE OLD FEATURES

Archive or delete:

- old banking-first flows
- old intelligence architecture
- vault-heavy systems
- old WhatsApp persona systems
- autonomous AI storefront generation
- old hackathon simulations
- complex Squad intelligence flows
- old storefront generation assumptions
- deep infrastructure assumptions
- abandoned integrations
- duplicated UI
- unused routes
- dead API endpoints
- legacy flows

Keep codebase clean.

Archive old experiments.

---

# AUTH SYSTEM

Authentication methods:

1. Email signup

Fields:

- name
- email
- phone number
- password

2. Google signup

Requirements:

- Google OAuth
- Auto-fill email
- Auto-fill name
- Request phone number after signup

Login:

- email login
- Google login
- forgot password

Goal:

Reduce onboarding friction.

---

# BUSINESS SETUP FLOW

After signup:

Collect:

Business Name

Business Type:

- Physical products
- Digital products
- Services

Business Description

Instagram Handle (optional)

WhatsApp Number

AI Assistance:

Button:

"Improve description"

AI only assists.

User remains fully in control.

---

# CORE MVP MODULES

## PRODUCTS MODULE

Fields:

- Product Name
- Price
- Stock Quantity
- Category
- Description
- Product Image

AI buttons:

- Improve title
- Generate description
- Suggest category

---

## ORDERS MODULE

Statuses:

- Pending
- Paid
- Delivered
- Cancelled

Fields:

Customer Name

Customer Phone

Order Amount

Products

Status

Created Date

Goal:

Reduce order chaos.

---

## INVENTORY MODULE

Fields:

Product

Stock Quantity

Low Stock Threshold

Low stock alerts:

Example:

⚠ Low stock

Goal:

Reduce inventory stress.

---

## CUSTOMERS MODULE

Fields:

Customer Name

Phone

Orders Count

Last Purchase

Goal:

Reduce customer tracking stress.

---

## NOTIFICATIONS MODULE

MVP notifications:

WhatsApp:

- New order
- Payment marked
- Low stock alert
- Daily summary

Dashboard notifications:

- New order
- Low stock
- Operational alerts

No conversational AI yet.

Simple first.

---

# DASHBOARD

Keep dashboard simple.

Top cards:

Orders Today

Revenue Today

Pending Orders

Low Stock Products

Sections:

Recent Orders

Low Stock Alerts

Customer Activity

AI Suggestions

Avoid:

- complex BI dashboards
- 20 charts
- unnecessary analytics

Operational visibility first.

---

# AI SYSTEM

AI is ASSISTIVE.

NOT autonomous.

AI helps:

- Product descriptions
- Product title improvements
- Category suggestions
- Description improvements
- Operational suggestions

Examples:

"You have 4 pending orders."

"Stock running low."

"Product descriptions missing."

AI DOES NOT:

- build full businesses
- generate frontend code
- make business decisions
- replace operations

Principle:

AI reduces friction.

User remains in control.

---

# DATABASE MODELS

Users

- id
- name
- email
- phone
- auth_provider
- created_at

Businesses

- id
- user_id
- business_name
- business_type
- instagram_handle
- whatsapp
- description

Products

- id
- business_id
- name
- description
- category
- price
- stock_quantity
- image_url

Orders

- id
- business_id
- customer_name
- customer_phone
- amount
- status
- created_at

Customers

- id
- business_id
- name
- phone
- total_orders
- last_purchase

Notifications

- id
- business_id
- type
- channel
- message

Inventory Movements

- id
- business_id
- product_id
- movement_type
- quantity

---

# BACKEND MODULES

backend/

auth/

users/

businesses/

products/

orders/

customers/

inventory/

notifications/

whatsapp/

ai/

shared/

No microservices.

Keep architecture simple.

---

# MVP BUILD ORDER

Phase 1

Auth

Business Setup

Dashboard Shell

Phase 2

Products

Orders

Inventory

Customers

Phase 3

WhatsApp Notifications

AI Assistance

Dashboard metrics

Phase 4

Testing

Bug fixing

Founder onboarding flow

---

# SUCCESS CRITERIA

MVP succeeds if:

Business creates account

Google signup works

Business profile setup works

Products added

Orders tracked

Inventory tracked

Customers tracked

WhatsApp notifications delivered

Dashboard usable

AI assistance usable

Everything else later.

---

# FINAL POSITIONING

AAJE is:

A business operations platform helping Nigerian businesses already selling online move away from scattered operational systems into one operational workspace.

Not another storefront.

Not another banking app.

Not another marketplace.

Operational simplicity for businesses already selling online.