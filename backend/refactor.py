import os
import shutil
import re

base_dir = r"c:\Users\anuoluwapo\OneDrive\Desktop\AAJE\backend\app"

moves = [
    # Auth
    (r"routes\auth.py", r"auth\routes.py"),
    # Storefront
    (r"routes\storefront.py", r"storefront\routes.py"),
    (r"services\storefront.py", r"storefront\service.py"),
    (r"services\ai_store_builder.py", r"storefront\ai_builder.py"),
    # Products
    (r"routes\product_routes.py", r"products\routes.py"),
    (r"services\product_service.py", r"products\service.py"),
    # Orders
    (r"routes\order_routes.py", r"orders\routes.py"),
    (r"services\order_service.py", r"orders\service.py"),
    # Inventory
    (r"services\inventory_service.py", r"inventory\service.py"),
    # Payments
    (r"routes\payments.py", r"payments\routes.py"),
    (r"services\squad.py", r"payments\squad.py"),
    (r"routes\squad_webhook.py", r"payments\webhook.py"),
    # WhatsApp
    (r"routes\webhook.py", r"whatsapp\routes.py"),
    (r"services\whatsapp_client.py", r"whatsapp\service.py"),
    (r"services\notifier.py", r"whatsapp\notifier.py"),
    # Campaigns
    (r"routes\marketing.py", r"campaigns\routes.py"),
    # BizPrint
    (r"routes\bizprint.py", r"bizprint\routes.py"),
    # AI
    (r"routes\ai_store_routes.py", r"ai\routes.py"),
    # Events
    (r"routes\events.py", r"events\routes.py"),
    (r"services\events.py", r"events\handlers.py"),
]

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

for src, dst in moves:
    src_path = os.path.join(base_dir, src)
    dst_path = os.path.join(base_dir, dst)
    if os.path.exists(src_path):
        ensure_dir(dst_path)
        print(f"Moving {src_path} -> {dst_path}")
        # Using git mv if it was tracked, but standard move is easier to write in python, 
        # then we can just git add/rm later. Let's stick to os.rename
        os.rename(src_path, dst_path)
    else:
        print(f"Not found: {src_path}")

print("Move operations completed.")
