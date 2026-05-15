import asyncio
import time

import httpx

from app.main import app


async def main():
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            health = await client.get("/health")
            print("health", health.status_code, health.json())

            suffix = str(int(time.time()))[-4:]
            payload = {
                "email": f"test{int(time.time())}@example.com",
                "password": "password123",
                "full_name": "Ada Okafor",
                "phone": f"+234 801 234 {suffix}",
                "business_description": "I sell natural skincare products to young professionals in Lagos",
            }
            signup = await client.post("/auth/signup", json=payload)
            print("signup", signup.status_code)
            data = signup.json()
            print("user_name", data.get("user", {}).get("full_name"))
            print("whatsapp_no", data.get("user", {}).get("whatsapp_no"))
            print("whatsapp_connected", data.get("user", {}).get("whatsapp_connected"))
            print("store_slug", data.get("store", {}).get("slug"))

            stores = await client.get(f"/api/storefront/stores/by-user/{data['user']['id']}")
            print("stores", stores.status_code, stores.json())


if __name__ == "__main__":
    asyncio.run(main())
