Here’s a detailed `about.md` your agent can use as the frontend product reference.

````md
# ABOUT AAJE

## Product Name
AAJE

## Product Category
AI-native storefront platform with conversational business operations through WhatsApp.

AAJE is not just a storefront builder.
AAJE is not just a WhatsApp bot.
AAJE is not just a payment tool.

AAJE is a commerce-first platform that helps African businesses create online storefronts, accept Squad-powered payments, manage inventory, receive WhatsApp sales notifications, and build measurable business identity through real commerce activity.

---

# 1. Product Summary

AAJE helps small businesses, creators, vendors, freelancers, and social commerce sellers move from scattered online selling to structured digital operations.

The user can:
1. Sign up.
2. Describe their business to AI.
3. Generate a storefront.
4. Add products or services.
5. Receive a path-based store link.
6. Accept Squad-powered payments.
7. Track orders and inventory.
8. Receive WhatsApp sales notifications.
9. Manage parts of the business conversationally.
10. Build a business activity profile called BizPrint.

---

# 2. Core One-Liner

AAJE lets African businesses create AI-powered storefronts, accept Squad payments, track operations, and manage their business through WhatsApp.

---

# 3. Main Product Hook

Create your AI-powered storefront and run your business through WhatsApp.

---

# 4. The Problem

Many African businesses already sell digitally through WhatsApp, Instagram, TikTok, Facebook, and referrals.

But they still manage operations manually through:
- chats
- screenshots
- notebooks
- memory
- scattered bank alerts

This causes:
- lost orders
- payment confirmation stress
- inventory confusion
- no sales visibility
- no campaign tracking
- no measurable business identity

AAJE structures this activity into a usable business system.

---

# 5. Target Users

AAJE is built for:
- WhatsApp sellers
- Instagram vendors
- social commerce businesses
- creators
- freelancers
- service providers
- campus vendors
- fashion sellers
- food vendors
- gadget sellers
- beauty brands
- SMEs

The target user is not necessarily illiterate.
The informal market includes educated, semi-formal, and digital-first sellers who still lack structured business operations.

---

# 6. Main User Story

A business owner signs up on AAJE.

The AI onboarding assistant asks what they sell, who they sell to, what style they want, and what products or services they offer.

AAJE generates a storefront with:
- store name
- tagline
- description
- preset layout
- categories
- starter products/services

The user edits or accepts the generated setup.

They connect payment setup through Squad sandbox.

They get a public link like:

```txt
aaje.store/thriftbyada
````

Customers visit the link, add products to cart, and pay through Squad.

When payment succeeds:

* order becomes paid
* inventory reduces
* dashboard updates
* WhatsApp sends sales notification
* BizPrint can update

The owner can later ask WhatsApp:

* what sold today?
* send my store link
* what is low in stock?
* show my sales
* withdraw funds

---

# 7. Product Direction

AAJE is commerce-first.

This means:

* storefront comes first
* inventory comes first
* orders come first
* payments come first
* WhatsApp supports operations
* BizPrint supports identity later

Do not design AAJE like a banking app.
Do not design AAJE like a marketplace.
Do not design AAJE like a generic chatbot.

Design it like:

* Shopify meets WhatsApp operations
* Bumpa-style storefront, but AI-native and conversational
* a modern commerce dashboard built for African social commerce

---

# 8. Key Differentiators

## 8.1 AI-Native Store Creation

Users do not start from blank templates.
They describe their business, and AAJE generates a usable store setup.

## 8.2 WhatsApp Operations

WhatsApp is an optional operational extension.

Users can receive notifications and, for premium features, manage the store conversationally.

## 8.3 Squad-Powered Payments

All storefront payments go through Squad.

Squad powers:

* checkout
* transaction verification
* webhooks
* transfers
* virtual accounts

## 8.4 Growth Attribution

Premium users can create campaign links to track where sales come from.

Example:

```txt
aaje.store/thriftbyada?ref=instagram
aaje.store/thriftbyada?ref=whatsapp_status
aaje.store/thriftbyada?ref=facebook_ad
```

AAJE tracks:

* visits
* orders
* conversions
* revenue by source

## 8.5 BizPrint

BizPrint is a private business activity score/profile.

It is built from:

* orders
* sales
* inventory activity
* payment behavior
* campaign conversion
* business consistency

BizPrint is not public.
It is visible to the business owner and may later support consent-based institutional access.

---

# 9. Final MVP Scope

The frontend should support:

## Must Have

* landing page
* signup/login
* AI onboarding assistant
* AI store generation preview
* pricing screen
* dashboard
* store setup/edit page
* product/service management
* inventory management
* public storefront page
* cart checkout
* payment success page
* WhatsApp settings
* campaign links page for premium
* BizPrint page or card
* AI help widget

## Should Have

* low stock display
* recent orders
* sales cards
* store preview card
* campaign performance preview
* premium upgrade prompts

## Not For MVP

* full marketplace
* delivery/logistics system
* customer accounts
* advanced drag-and-drop builder
* AI image generation
* voice notes
* mobile app
* advanced accounting
* full ERP inventory

---

# 10. Main Pages To Build

## 10.1 Landing Page

Purpose:
Explain what AAJE is and convert users.

Sections:

* hero
* problem
* AI storefront creation
* WhatsApp operations
* Squad payments
* campaign tracking
* BizPrint
* pricing preview
* CTA

Hero wording:

```txt
Create your AI-powered storefront and run your business through WhatsApp.
```

Subtext:

```txt
AAJE helps African businesses sell online, accept Squad payments, track inventory, and manage operations conversationally.
```

Primary CTA:

```txt
Create Your Store
```

Secondary CTA:

```txt
See How It Works
```

---

## 10.2 Signup Page

Authentication options:

* Google signup
* email signup

If user selects email signup:

* collect phone number

For hackathon:
No real verification required.

Fields:

* name
* email
* phone
* password

---

## 10.3 AI Onboarding Page

This page should feel like the AI is helping the user build the business.

AI asks:

1. What do you sell or offer?
2. Is it a product or service business?
3. Who are your customers?
4. What style do you want?
5. What products/services should we start with?

Style options:

* simple
* premium
* playful
* local
* clean

The UI should include:

* chat-like assistant panel
* progress indicator
* generated preview area
* continue button

---

## 10.4 AI Store Preview Page

After AI generation, show:

* generated store name
* tagline
* description
* categories
* starter products/services
* selected layout
* store preview

Actions:

* Accept
* Edit
* Regenerate
* Continue

Important:
Pricing should appear after the user sees generated value.

---

## 10.5 Pricing Page

Pricing appears after the AI store preview and before publishing.

Plans:

### Free — Start

Best for starting online.

Includes:

* 1 storefront
* basic inventory
* Squad payments
* basic dashboard
* daily WhatsApp sales notification
* basic BizPrint

### Premium — Grow

Price:

```txt
₦3,000/month
```

Includes:

* campaign analytics
* advanced WhatsApp operations
* AI insights
* growth intelligence
* richer BizPrint
* advanced analytics
* multiple storefronts later

CTA:

* Continue with Free
* Upgrade to Grow

Design note:
Premium should feel valuable, but free should not feel useless.

---

## 10.6 Dashboard

This is the main business control center.

Top cards:

* Today Sales
* Total Revenue
* Orders
* BizPrint Score

Sections:

* recent orders
* products and stock
* low stock
* store preview
* store link
* WhatsApp notification settings
* recent transactions
* AI insight card
* premium upgrade card

Free users see:

* basic sales
* recent orders
* daily WhatsApp notification setting
* basic BizPrint

Premium users see:

* campaign analytics
* advanced insights
* WhatsApp operations
* detailed BizPrint

---

## 10.7 Product / Service Management

Products and services use the same model.

Fields:

* name
* type: product or service
* description
* category
* price
* image upload
* stock quantity
* low stock threshold
* active/inactive

For services:

* stock can be optional or null

Actions:

* add product/service
* edit
* delete
* mark active/inactive

---

## 10.8 Inventory Page

Keep inventory simple.

Show:

* product name
* current stock
* low stock threshold
* stock status
* manual stock adjustment

Stock statuses:

* In Stock
* Low Stock
* Out of Stock

Rules:

* stock reduces only after successful payment
* no checkout if stock is zero
* low-stock alert if stock <= threshold

---

## 10.9 Public Storefront Page

Public path format:

```txt
aaje.store/{slug}
```

Example:

```txt
aaje.store/thriftbyada
```

The storefront should show:

* store banner
* store name
* tagline
* description
* product/service grid
* product details
* add to cart
* cart drawer
* checkout button
* WhatsApp/contact seller button
* Squad payment trust indicator

Design:

* mobile-first
* clean
* social-commerce friendly
* simple

---

## 10.10 Cart + Checkout

Guest checkout only.

Cart rules:

* maximum 4 products
* if more than 4, show message:

```txt
You can checkout with up to 4 items at once.
```

Customer fields:

* name
* phone
* optional note

Payment flow:

1. customer adds products
2. customer enters details
3. order is created as pending
4. user pays through Squad
5. payment succeeds
6. order marked paid
7. inventory reduces

Checkout should be fast and clean.

---

## 10.11 Payment Success Page

Show:

* payment successful
* order summary
* customer name
* amount paid
* store name
* next step message

Example:

```txt
Payment successful. Your order has been sent to the seller.
```

---

## 10.12 WhatsApp Settings Page

WhatsApp is optional.

Free users:

* can enable daily sales notification
* default time is 8PM

Fields:

* WhatsApp number
* notification enabled
* daily summary time

Free users get:

* daily sales summary
* basic order/payment notifications

Premium users get:

* advanced WhatsApp operations
* inventory updates
* product creation
* order management
* withdrawal actions

---

## 10.13 Campaign Links Page

Premium only.

Purpose:
Track where customers come from.

Sources:

* Instagram
* WhatsApp Status
* Facebook
* TikTok
* Custom

User flow:

1. select source
2. generate link
3. copy link
4. share manually

Example link:

```txt
aaje.store/thriftbyada?ref=instagram
```

Metrics:

* visits
* orders
* revenue
* conversion rate
* best-performing channel

Free users should see locked preview with upgrade CTA.

---

## 10.14 BizPrint Page / Card

BizPrint is a private business activity score.

Show:

* BizPrint score
* label
* simple explanation
* score factors

Example labels:

* Building
* Active
* Growing
* Reliable

Free users:

* see basic score only

Premium users:

* see breakdown and recommendations

Do not make BizPrint feel like a bank credit score.
It is business activity identity.

---

## 10.15 AI Help Widget

The dashboard should include an AI bot button.

Purpose:

* navigation
* explanations
* simple help

Example questions:

* how do I add products?
* what is BizPrint?
* how do I connect WhatsApp?
* how do campaign links work?
* where do I see orders?

Free:

* navigation help only

Premium:

* operational insights and suggestions

The AI help widget should not behave like a general chatbot.
It should only answer AAJE/business operations questions.

---

# 11. User Flow

## Main Flow

```txt
User signs up
↓
AI assistant asks business questions
↓
AI generates store
↓
User previews and tweaks
↓
Pricing appears
↓
User selects Free or Premium
↓
User connects payment/account setup
↓
Store is published
↓
User gets path-based store link
↓
Customer buys through Squad checkout
↓
Dashboard updates
↓
WhatsApp notification is sent
```

---

# 12. Free vs Premium

## Free — Start

Purpose:
Let users start selling.

Access:

* 1 store
* AI store generation
* product/service listings
* cart checkout
* Squad payments
* basic inventory
* basic dashboard
* basic BizPrint
* daily WhatsApp sales notification

Limitations:

* no campaign links
* no advanced analytics
* no advanced WhatsApp operations
* no AI operational insights
* no detailed BizPrint
* no multiple stores

---

## Premium — Grow

Price:

```txt
₦3,000/month
```

Purpose:
Help businesses operate and grow intelligently.

Access:

* campaign links
* conversion analytics
* advanced dashboard
* detailed BizPrint
* AI operational insights
* advanced WhatsApp operations
* richer growth analytics
* multiple stores later

---

# 13. Campaign Links

Campaign links are premium-only.

They are not ads.
They are attribution links.

Example:

```txt
aaje.store/thriftbyada?ref=instagram
```

They help users understand:

* where visitors came from
* what source converts
* what channel generates revenue

This supports growth intelligence and BizPrint later.

---

# 14. Path-Based Routing

Use path-based storefront URLs.

Use:

```txt
aaje.store/{slug}
```

Do not use subdomains for MVP.

Examples:

* aaje.store/thriftbyada
* aaje.store/yusufgadgets
* aaje.store/adafoodhub

Slug rules:

* unique
* lowercase
* URL-safe
* generated from store name

---

# 15. Design Direction

The frontend should feel:

* modern
* clean
* AI-native
* mobile-first
* commerce-first
* operational
* simple
* African-business aware

Avoid:

* bank app look
* crypto aesthetic
* overly corporate layout
* cluttered marketplace feel

Visual inspiration:

* Shopify
* Stripe
* Linear
* Notion
* Paystack
* Moniepoint-style clarity

---

# 16. Frontend Tone

Use direct, simple language.

Examples:

Instead of:

```txt
Configure your commerce infrastructure
```

Use:

```txt
Set up your store
```

Instead of:

```txt
Enable operational notification layer
```

Use:

```txt
Get WhatsApp sales updates
```

Instead of:

```txt
Economic identity metrics
```

Use:

```txt
Your BizPrint score
```

---

# 17. Dashboard Copy Examples

Cards:

* Today’s Sales
* Total Revenue
* Orders
* BizPrint

Buttons:

* Add Product
* Preview Store
* Copy Store Link
* Connect WhatsApp
* Upgrade to Grow
* Generate Campaign Link

Empty states:

* No products yet. Add your first product to publish your store.
* No orders yet. Share your store link to start selling.
* Connect WhatsApp to receive daily sales updates.

---

# 18. Important UX Rules

1. Store creation must feel fast.
2. AI should reduce work, not add complexity.
3. Free users must feel value quickly.
4. Premium should feel like growth power.
5. WhatsApp should feel optional but useful.
6. BizPrint should feel simple, not intimidating.
7. Checkout should be clean and fast.
8. Dashboard should show only useful business data.

---

# 19. Final Product Identity

AAJE is:

```txt
AI-native storefronts + WhatsApp business operations + Squad-powered commerce.
```

The frontend must make this obvious within the first 30 seconds.

```
```
