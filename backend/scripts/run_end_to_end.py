import asyncio
import uuid
from decimal import Decimal

from app.database import engine, Base, AsyncSessionLocal
from app.models.user import User
from app.services.ai_store_builder import generate_store_payload, create_store
from app.services.product_service import create_product, list_products
from app.services.order_service import create_order, mark_order_paid
from app.services.squad_payment_service import create_payment_link


async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Create a test user
        user = User(whatsapp_no="+2340000000000", full_name="Test Trader")
        session.add(user)
        await session.flush()

        # Generate AI payload
        payload = await generate_store_payload({"business_type": "thrift clothes", "preferred_style": "clean"})

        # Create store and starter product(s)
        store = await create_store(session, user.id, payload, create_products=True)
        print("Created store:", store.store_name, str(store.id))

        # List products
        products = await list_products(session, store.id)
        print("Starter products:")
        for p in products:
            print(" -", p.name, "stock:", p.stock_quantity, "price:", float(p.price or 0))

        # Create an order for the first product; ensure stock available
        if not products:
            print("No products to order.")
            return
        prod = products[0]
        if prod.stock_quantity <= 0:
            print("Starter product has zero stock; topping up to 10 for test.")
            prod.stock_quantity = 10
            await session.flush()
        customer = {"name": "Customer A", "phone": "+2341111111111"}
        items = [{"product_id": str(prod.id), "quantity": 1}]
        order = await create_order(session, store.id, customer, items)
        print("Created order:", order.id, "total:", float(order.total_amount))

        # Create payment link (simulated)
        link = await create_payment_link(order.id, float(order.total_amount))
        print("Payment link:", link)

        # Simulate webhook -> mark order paid
        await mark_order_paid(session, order.id, squad_ref=link["reference"])
        print("Marked order paid."
              )

        # Check product stock after sale
        products_after = await list_products(session, store.id)
        for p in products_after:
            print("Product", p.name, "stock after:", p.stock_quantity)


if __name__ == "__main__":
    asyncio.run(run())
