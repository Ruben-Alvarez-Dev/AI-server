from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
import os
import json
import asyncio
from typing import Optional, Dict, Any

router = APIRouter()

OPENAI_API_KEY = os.getenv("sk-test_FAKE_6b8f2a4d9c3e7f1a2b0c")

# Helper: simple auth
def authorize(authorization: Optional[str]):
    if OPENAI_API_KEY:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
        token = authorization.split(" ", 1)[1]
        if token != OPENAI_API_KEY:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(None)):
    """
    OpenAI-compatible /v1/chat/completions adapter.
    - Auth: Bearer token via OPENAI_COMPAT_API_KEY
    - Maps messages -> single request string and dispatches to internal RequestManager.execute_workflow
    - Supports 'stream' param: when true, returns a simple streaming response. (Incremental token streaming will be simulated if internal workflow doesn't stream.)
    """
    authorize(authorization)
    body = await request.json()
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    model = body.get("model")
    # Build prompt from messages
    prompt = "\n".join(m.get("content", "") for m in messages)

    # Get request manager
    request_mgr = request.app.state.request_manager
    if not request_mgr:
        raise HTTPException(status_code=500, detail="Request manager not initialized")

    # Execute workflow (auto-detect workflow)
    async def run_workflow():
        res = await request_mgr.execute_workflow(prompt, workflow_type=None, context=body.get("context", {}))
        return res

    if not stream:
        res = await run_workflow()
        # Map internal result to OpenAI response shape
        content = ""
        if isinstance(res.get("result"), dict):
            # if the workflow result is structured, stringify appropriately
            content = json.dumps(res.get("result"))
        else:
            content = str(res.get("result", ""))

        return {
            "id": res.get("request_id"),
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop"
                }
            ],
            "usage": {}  # Optional: fill with tokens if available
        }
    else:
        # Streaming response: yield the final content as a single chunk (best-effort)
        async def event_stream():
            res = await run_workflow()
            if isinstance(res.get("result"), dict):
                content = json.dumps(res.get("result"))
            else:
                content = str(res.get("result", ""))
            # Simple chunked stream: yield in small slices
            chunk_size = 256
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                # OpenAI server-sent style chunk with data: prefix
                yield f"data: {json.dumps({'choices':[{'delta': {'content': chunk}}]})}\n\n"
                await asyncio.sleep(0.01)
            # final event
            yield f"data: {json.dumps({'choices':[{'finish_reason':'stop'}]})}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/v1/completions")
async def completions(request: Request, authorization: Optional[str] = Header(None)):
    """Compatibility for legacy /v1/completions — mapped to same workflow as chat completions."""
    authorize(authorization)
    body = await request.json()
    prompt = body.get("prompt") or ""
    # Reuse logic from chat
    req = request.scope
    # Reuse request manager
    request_mgr = request.app.state.request_manager
    if not request_mgr:
        raise HTTPException(status_code=500, detail="Request manager not initialized")

    res = await request_mgr.execute_workflow(prompt, workflow_type=None, context=body.get("context", {}))
    content = res.get("result")
    if isinstance(content, dict):
        content = json.dumps(content)
    return {
        "id": res.get("request_id"),
        "object": "text.completion",
        "choices": [{"text": str(content), "index": 0, "finish_reason": "stop"}],
        "usage": {}
    }


@router.post("/v1/embeddings")
async def embeddings(request: Request, authorization: Optional[str] = Header(None)):
    """
    Embeddings endpoint.
    - Attempts to call a workflow_type 'embeddings' via RequestManager
    - If no embeddings workflow is available, returns 501
    """
    authorize(authorization)
    body = await request.json()
    input_data = body.get("input")
    if input_data is None:
        raise HTTPException(status_code=400, detail="Missing 'input' field")

    request_mgr = request.app.state.request_manager
    if not request_mgr:
        raise HTTPException(status_code=500, detail="Request manager not initialized")

    # Try to invoke workflow type 'embeddings'
    res = await request_mgr.execute_workflow(str(input_data), workflow_type="embeddings", context={"input": input_data})
    if res.get("status") == "failed":
        # Not implemented on internal side
        raise HTTPException(status_code=501, detail="Embeddings workflow not implemented internally")
    # Expect res.result to contain embeddings vector or list
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": res.get("result"),
                "index": 0
            }
        ]
    }
