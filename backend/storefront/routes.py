from fastapi import APIRouter
from .ai_store_builder import router as ai_router
from .products import router as products_router
from .orders import router as orders_router
from .inventory import router as inventory_router
from .service import router as store_router

router = APIRouter()
router.include_router(ai_router, prefix="/ai")
router.include_router(store_router, prefix="/stores")
router.include_router(products_router, prefix="/products")
router.include_router(orders_router, prefix="/orders")
router.include_router(inventory_router, prefix="/inventory")
