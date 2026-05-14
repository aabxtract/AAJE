from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Store, Product
from app.services.order_service import create_order
from app.services.squad_payment_service import create_payment_link

router = APIRouter(tags=["public_store"]) 


@router.get("/store/{slug}", response_class=HTMLResponse)
async def store_home(slug: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute("SELECT * FROM stores WHERE slug = :slug", {"slug": slug})
    row = q.first()
    if not row:
        raise HTTPException(status_code=404, detail="Store not found")
    store = await db.get(Store, row[0]) if False else None
    # fetch store by slug properly
    q2 = await db.execute("SELECT id, store_name, description FROM stores WHERE slug = :slug", {"slug": slug})
    srow = q2.first()
    store_id = srow[0]
    store_name = srow[1]
    description = srow[2] or ""

    # fetch products
    q3 = await db.execute("SELECT id, name, price, stock_quantity FROM products WHERE store_id = :sid AND is_active = true", {"sid": store_id})
    products = q3.fetchall()

    items_html = "".join(
        f"<li><a href=\"/store/{slug}/product/{p[0]}\">{p[1]}</a> — ₦{float(p[2] or 0):.2f} — stock: {p[3]}</li>"
        for p in products
    )

    html = f"""
    <html><head><title>{store_name}</title></head>
    <body>
    <h1>{store_name}</h1>
    <p>{description}</p>
    <h2>Products</h2>
    <ul>
    {items_html}
    </ul>
    </body></html>
    """
    return HTMLResponse(content=html)


@router.get("/store/{slug}/product/{product_id}", response_class=HTMLResponse)
async def product_detail(slug: str, product_id: str, db: AsyncSession = Depends(get_db)):
    # fetch product
    q = await db.execute("SELECT id, name, description, price, stock_quantity FROM products WHERE id = :pid", {"pid": product_id})
    p = q.first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    html = f"""
    <html><head><title>{p[1]}</title></head>
    <body>
    <h1>{p[1]}</h1>
    <p>{p[2]}</p>
    <p>Price: ₦{float(p[3] or 0):.2f}</p>
    <p>Stock: {p[4]}</p>
    <form action="/store/{slug}/checkout" method="post">
      <input type="hidden" name="product_id" value="{p[0]}" />
      <label>Your name: <input name="customer_name" /></label><br/>
      <label>Your phone: <input name="customer_phone" /></label><br/>
      <label>Quantity: <input name="quantity" value="1" /></label><br/>
      <button type="submit">Pay</button>
    </form>
    </body></html>
    """
    return HTMLResponse(content=html)


@router.post("/store/{slug}/checkout", response_class=HTMLResponse)
async def checkout(
    request: Request,
    slug: str,
    product_id: str = Form(...),
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    quantity: int = Form(1),
    db: AsyncSession = Depends(get_db),
):
    # find store
    q = await db.execute("SELECT id FROM stores WHERE slug = :slug", {"slug": slug})
    srow = q.first()
    if not srow:
        raise HTTPException(status_code=404, detail="Store not found")
    store_id = srow[0]

    items = [{"product_id": product_id, "quantity": quantity}]
    customer = {"name": customer_name, "phone": customer_phone}
    order = await create_order(db, store_id, customer, items)
    link = await create_payment_link(order.id, float(order.total_amount))

    html = f"""
    <html><body>
    <h1>Pay for order {order.id}</h1>
    <p>Total: ₦{float(order.total_amount):.2f}</p>
    <p><a href=\"{link['url']}\">Click here to pay</a></p>
    <p>Or use this payment reference: {link['reference']}</p>
    </body></html>
    """
    return HTMLResponse(content=html)
