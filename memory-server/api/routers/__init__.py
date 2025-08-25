"""
API Routers for Memory-Server
"""

from .health import router as health_router
from .documents import router as documents_router
from .web_search import router as web_search_router

# Future routers (not implemented yet)
# from .ingest import router as ingest_router
# from .search import router as search_router  
# from .memory import router as memory_router
# from .admin import router as admin_router

__all__ = [
    "health_router",
    "documents_router",
    "web_search_router"
    # "ingest_router",
    # "search_router", 
    # "memory_router",
    # "admin_router"
]