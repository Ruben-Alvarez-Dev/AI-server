"""
ATLAS Server Package
Provides HTTP server for ATLAS black-box system.

IMPORTANT:
- Only public endpoints are documented and accessible
- Internal implementation is completely opaque
- All processing happens through black-box algorithms

Server endpoints:
- POST /atlas/v1/process - Process content
- POST /atlas/v1/enhance - Enhance content  
- GET /atlas/v1/status - System status
- GET /atlas/health - Health check
"""

__version__ = "1.0.0"
__author__ = "Ruben-Alvarez-Dev"

# Note: Internal ATLAS server implementation is opaque