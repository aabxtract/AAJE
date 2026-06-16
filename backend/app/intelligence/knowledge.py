"""Intent-aware knowledge injection — CLAUDE.md §7 (System 4).

Not RAG for MVP. Each section is a short text snippet (<500 chars) that the
agent loop pipes into the ``{relevant_knowledge}`` slot of the system prompt.

Upgrade path: replace ``get_knowledge_for()`` with a pgvector lookup against
a Supabase ``knowledge`` table. The interface stays a single ``str`` return,
so no callers change.
"""
from __future__ import annotations


_SECTIONS = {
    "bizprint": (
        "BizPrint is the trader's financial identity score (0–100). "
        "Computed from 4 components, each 0–25: consistency (active days), "
        "volume (avg daily revenue vs ₦50k), growth (last 30 vs prior 30 "
        "days), tenure (days on AAJE vs 90). Grades: A+ (91+, ₦500k loan), "
        "A (81+, ₦350k), B+ (71+, ₦200k), B (61+, ₦150k), C+ (51+, ₦75k), "
        "C (41+, ₦30k), D (<41, ₦0). AAJE does NOT issue loans — BizPrint "
        "is shown to partner lenders; lender decision is independent."
    ),
    "payments": (
        "MVP: customers pay by direct bank transfer to the trader's account "
        "on file. There is no AAJE wallet to withdraw from — money lands on "
        "the trader's bank account directly. Buyer clicks 'I've Transferred' "
        "on the storefront → trader gets a WhatsApp alert with order ref and "
        "amount → trader checks their bank app → replies 'confirm AAJE-X' or "
        "'reject AAJE-X'. The 'balance' command shows total confirmed sales "
        "this month. Automated payments via Monnify return next month after CAC."
    ),
    "orders": (
        "Order flow (MVP): customer places order on storefront → status "
        "'pending' → customer transfers manually + clicks 'I've Transferred' → "
        "status 'transfer_claimed' → trader gets WhatsApp alert → trader "
        "checks bank → replies 'confirm AAJE-XXXX' (status 'confirmed') or "
        "'reject AAJE-XXXX' (status 'rejected'). After fulfilling: "
        "'delivered AAJE-XXXX' → status 'delivered'. Chat commands: orders, "
        "confirm AAJE-X, reject AAJE-X, delivered AAJE-X, balance, menu. "
        "The bot only messages the trader — trader-to-buyer follow-up uses "
        "the wa.me link inside the trader's notification."
    ),
    "store": (
        "Each trader has one storefront at aaje.store/store/{slug}. The AI "
        "generated it from their plain-text business description at signup "
        "(store name, theme colors, products). For MVP, products are added "
        "and edited from the AAJE dashboard (adding via chat returns next "
        "month). Storefront is the canonical product list — customers browse "
        "there, place orders there, and see the trader's bank account at "
        "checkout for manual transfer."
    ),
    "general": (
        "AAJE is a WhatsApp-native business OS for Nigerian traders. "
        "One web storefront + one WhatsApp command center, sharing one "
        "BizPrint score and one trader account. Anything done on web "
        "shows on WhatsApp instantly, and vice versa. MVP uses manual "
        "bank transfer; automated payments + chat-based product/withdrawal "
        "actions return after the CAC + Monnify integration next month."
    ),
}


_INTENT_TO_SECTION = {
    "bizprint": "bizprint",
    "score": "bizprint",
    "loan": "bizprint",
    "credit": "bizprint",

    "balance": "payments",
    "wallet": "payments",
    "money": "payments",
    "withdraw": "payments",
    "payment": "payments",
    "pay": "payments",

    "order": "orders",
    "sale": "orders",
    "customer": "orders",
    "delivered": "orders",
    "pending": "orders",

    "store": "store",
    "product": "store",
    "link": "store",
    "share": "store",
    "add": "store",
}


def detect_intent_for_knowledge(message: str) -> str:
    """Return one of: bizprint | payments | orders | store | general."""
    text = (message or "").lower()
    for keyword, section in _INTENT_TO_SECTION.items():
        if keyword in text:
            return section
    return "general"


def get_knowledge_for(intent: str) -> str:
    """Return the knowledge snippet for an intent. Falls back to 'general'."""
    return _SECTIONS.get(intent, _SECTIONS["general"])
