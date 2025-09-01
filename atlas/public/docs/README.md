# ATLAS Public Interface Documentation

## Overview

ATLAS is a black-box enhancement system that provides intelligent content processing capabilities. This documentation covers **ONLY** the public interfaces - internal implementation is completely opaque.

## Public Interfaces

### Available Endpoints

- `POST /atlas/v1/process` - Process content through ATLAS
- `POST /atlas/v1/enhance` - Enhance content quality
- `GET /atlas/v1/status` - Check ATLAS system status
- `GET /atlas/health` - Health check endpoint

### Request/Response Schemas

All schemas are defined in `/atlas/public/schemas/` directory.

### Integration Points

ATLAS integrates with:
- Memory Server (content enhancement)
- LLM Server (response improvement)
- GUI Server (real-time processing)

## Usage Examples

```python
# Basic ATLAS integration
from atlas.public.interfaces import atlas_process

result = await atlas_process({
    "input": "content to process",
    "mode": "enhance",
    "options": {}
})
```

## Important Notes

- ATLAS internal implementation is completely opaque
- Only use documented public interfaces
- Do not attempt to access /atlas/core/ contents
- All functionality is provided through public APIs