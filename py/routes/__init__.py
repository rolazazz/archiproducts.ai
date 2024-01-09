# makes "routers" a "Python subpackage"

from fastapi import APIRouter
from .test import test_router
from .visualsearch import visualsearch_router

router = APIRouter()

router.include_router(visualsearch_router)
router.include_router(test_router)
