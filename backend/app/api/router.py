"""
API Router Aggregator
Combines all modular routers (Auth, Layer 1, Layer 2, Layer 3) under /api/v1.
"""

from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.layer1 import router as layer1_router
from app.api.layer2 import router as layer2_router
from app.api.layer3 import router as layer3_router
from app.api.layer4 import router as layer4_router
from app.api.layer5 import router as layer5_router
from app.api.layer6 import router as layer6_router
from app.api.layer7 import router as layer7_router
from app.api.layer8 import router as layer8_router
from app.api.layer9 import router as layer9_router
from app.api.layer10 import router as layer10_router
from app.api.cogent import router as cogent_router
from app.api.sessions import router as sessions_router
from app.api.documents import router as documents_router
from app.api.telemetry import router as telemetry_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(sessions_router)
api_router.include_router(documents_router)
api_router.include_router(layer1_router)
api_router.include_router(layer2_router)
api_router.include_router(layer3_router)
api_router.include_router(layer4_router)
api_router.include_router(layer5_router)
api_router.include_router(layer6_router)
api_router.include_router(layer7_router)
api_router.include_router(layer8_router)
api_router.include_router(layer9_router)
api_router.include_router(layer10_router)
api_router.include_router(cogent_router)
api_router.include_router(telemetry_router)


