import os
import re

base_dir = r"c:\Users\anuoluwapo\OneDrive\Desktop\AAJE\backend\app"

import_mappings = {
    r"from app\.routes\.auth": "from app.auth.routes",
    r"import app\.routes\.auth": "import app.auth.routes",
    
    r"from app\.routes\.storefront": "from app.storefront.routes",
    r"import app\.routes\.storefront": "import app.storefront.routes",
    r"from app\.services\.storefront": "from app.storefront.service",
    r"from app\.services\.ai_store_builder": "from app.storefront.ai_builder",
    
    r"from app\.routes\.product_routes": "from app.products.routes",
    r"from app\.services\.product_service": "from app.products.service",
    
    r"from app\.routes\.order_routes": "from app.orders.routes",
    r"from app\.services\.order_service": "from app.orders.service",
    
    r"from app\.services\.inventory_service": "from app.inventory.service",
    
    r"from app\.routes\.payments": "from app.payments.routes",
    r"from app\.services\.squad": "from app.payments.squad",
    r"from app\.routes\.squad_webhook": "from app.payments.webhook",
    
    r"from app\.routes\.webhook": "from app.whatsapp.routes",
    r"from app\.services\.whatsapp_client": "from app.whatsapp.service",
    r"from app\.services\.notifier": "from app.whatsapp.notifier",
    
    r"from app\.routes\.marketing": "from app.campaigns.routes",
    
    r"from app\.routes\.bizprint": "from app.bizprint.routes",
    
    r"from app\.routes\.ai_store_routes": "from app.ai.routes",
    
    r"from app\.routes\.events": "from app.events.routes",
    r"from app\.services\.events": "from app.events.handlers",
}

for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            original_content = content
            for old, new in import_mappings.items():
                content = re.sub(old + r"(?=\s|import|$)", new, content)
                
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Updated imports in {file_path}")

print("Import fixing completed.")
