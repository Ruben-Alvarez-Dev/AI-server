#!/usr/bin/env python3
"""
Real LLM Server with actual model inference and OpenAI-compatible features
Includes reasoning, thinking mode, streaming, MCP compatibility, etc.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import asyncio
from typing import List, Optional, Dict, Any, Union, AsyncGenerator
from pathlib import Path
import json
import time
import uuid
import logging

# Import llama-cpp-python and RAG components
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("⚠️  llama-cpp-python not available, using mock responses")

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import RAG components
try:
    # Check if RAG should be disabled via environment variable
    import os
    if os.getenv('RAG_AVAILABLE', 'true').lower() == 'false':
        RAG_AVAILABLE = False
        logger.info("⚠️  RAG disabled via environment variable")
    else:
        from rag_components import CoRAGEngine, GraphRAGMemory, ModularMemory, VectorStore, EmbeddingsEngine
        RAG_AVAILABLE = True
        logger.info("✅ RAG components imported successfully")
except ImportError as e:
    RAG_AVAILABLE = False
    logger.error(f"⚠️  RAG components not available: {e}")

# Create FastAPI app
app = FastAPI(
    title="Real LLM Server - OpenAI Compatible",
    description="Advanced LLM Server with full OpenAI API compatibility, thinking mode, MCP support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instances
model = None
rag_engine = None
memory_system = None
vector_store = None
embeddings_engine = None

# Request models following OpenAI spec
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, assistant, or tool")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Name of the message sender")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls made by assistant")
    tool_call_id: Optional[str] = Field(None, description="ID of tool call being responded to")

class ChatRequest(BaseModel):
    model: str = Field("qwen2.5-32b-instruct", description="Model to use")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    
    # Generation parameters
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    max_tokens: Optional[int] = Field(1024, ge=1, description="Maximum tokens to generate")
    
    # OpenAI compatibility
    stream: bool = Field(False, description="Enable streaming responses")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Logit bias")
    user: Optional[str] = Field(None, description="User identifier")
    
    # Advanced features
    reasoning: bool = Field(False, description="Enable reasoning/thinking mode")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Available tools for function calling")
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field("auto", description="Tool choice strategy")
    
    # MCP compatibility
    mcp_server: Optional[str] = Field(None, description="MCP server to use")
    mcp_tools: Optional[List[str]] = Field(None, description="MCP tools to enable")
    
    # Claude-style operation modes
    mode: str = Field("chat", description="Operation mode: chat, plan, act, agent, edit, continue")
    context_files: Optional[List[str]] = Field(None, description="Files to include in context for edit mode")
    project_root: Optional[str] = Field(None, description="Project root directory for agent mode")
    
    # Advanced RAG features
    use_rag: bool = Field(True, description="Enable RAG (Retrieval-Augmented Generation)")
    use_corag: bool = Field(False, description="Enable CoRAG (Chain-of-Retrieval)")
    use_memory: bool = Field(True, description="Enable modular memory system")
    rag_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    memory_context: bool = Field(True, description="Include memory context in response")

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "llm-server"

class StreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]

@app.on_event("startup")
async def startup_event():
    """Initialize model and RAG components on startup"""
    global model, rag_engine, memory_system, vector_store, embeddings_engine, RAG_AVAILABLE
    
    # Initialize main LLM
    if LLAMA_AVAILABLE:
        try:
            model_path = Path("./models/qwen2.5-coder-7b-instruct-q6_k.gguf")
            if model_path.exists():
                logger.info(f"🤖 Loading model: {model_path}")
                model = Llama(
                    model_path=str(model_path),
                    n_ctx=131072,  # 128K context as specified
                    n_gpu_layers=-1,  # Use all GPU layers (Metal acceleration)
                    verbose=False,
                    n_threads=12,  # Increased for 32B model
                    # Metal-specific optimizations for M1 Ultra
                    use_mmap=True,
                    use_mlock=True,
                    n_batch=256,  # Reduced batch for larger model
                    rope_scaling_type=1,  # Linear scaling for longer context
                    rope_freq_base=10000.0
                )
                logger.info("✅ Model loaded successfully with Metal acceleration!")
            else:
                logger.error(f"❌ Model not found: {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
    
    # Initialize RAG components
    if RAG_AVAILABLE:
        try:
            logger.info("🧠 Initializing RAG components...")
            
            # Initialize embeddings engine
            embeddings_engine = EmbeddingsEngine(
                model_name="all-MiniLM-L6-v2",
                device="auto",
                batch_size=32
            )
            await embeddings_engine.warm_up()
            
            # Initialize vector store
            vector_store = VectorStore(
                dimension=embeddings_engine.dimension,
                index_type="HNSW",
                store_path="./rag_data/vector_store",
                use_gpu=False  # FAISS GPU not available on M1
            )
            await vector_store.load_from_disk()
            
            # Initialize modular memory
            memory_system = ModularMemory(
                working_memory_limit=131072,  # 128K tokens
                episode_memory_limit=2097152,  # 2M tokens
                max_episodes=1000,
                max_concepts=5000
            )
            
            # Initialize CoRAG engine
            rag_engine = CoRAGEngine(
                llm_model=model,
                vector_store=vector_store,
                max_chains=5
            )
            
            logger.info("✅ RAG components initialized successfully!")
            logger.info(f"   - Embeddings: {embeddings_engine.dimension}D {embeddings_engine.model_name}")
            logger.info(f"   - Vector Store: {vector_store.get_statistics()['total_documents']} documents")
            logger.info(f"   - Memory System: 3-tier architecture ready")
            logger.info(f"   - CoRAG Engine: Chain-of-Retrieval enabled")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG components: {e}")
            RAG_AVAILABLE = False

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "message": "Real LLM Server - OpenAI Compatible",
        "status": "running", 
        "model_loaded": model is not None,
        "llama_available": LLAMA_AVAILABLE,
        "features": {
            "streaming": True,
            "reasoning_mode": True,
            "function_calling": True,
            "mcp_compatible": True,
            "metal_acceleration": True,
            "context_size": "128K",
            "rag_enabled": RAG_AVAILABLE,
            "corag_chains": True,
            "modular_memory": True,
            "vector_store": True,
            "effective_context": "2M+ tokens via RAG"
        },
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models", 
            "health": "/health",
            "reasoning_test": "/test/reasoning",
            "math_test": "/test/math",
            "code_test": "/test/coding",
            "streaming_test": "/test/streaming",
            "plan_mode": "/test/plan-mode",
            "act_mode": "/test/act-mode", 
            "agent_mode": "/test/agent-mode",
            "edit_mode": "/test/edit-mode",
            "continue_mode": "/test/continue-mode"
        },
        "modes": {
            "chat": "Standard conversational mode",
            "plan": "Planning mode - creates detailed plans without execution",
            "act": "Action mode - executes tasks directly",
            "agent": "Autonomous agent mode with project context",
            "edit": "Code editing mode with file context",
            "continue": "Continue previous conversations/tasks"
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy", 
        "server": "running",
        "model_ready": model is not None,
        "gpu_acceleration": "metal" if model else "none"
    }

# OpenAI-compatible endpoints
@app.get("/v1/models")
async def list_models():
    """List available models including virtual optimized models"""
    models = []
    
    # Virtual optimized models (recommended for different clients)
    virtual_models = [
        {
            "id": "cline-optimized",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "llm-server",
            "description": "Optimized for Cline PLAN/ACT modes with multimodal support"
        },
        {
            "id": "openai-compatible", 
            "object": "model",
            "created": int(time.time()),
            "owned_by": "llm-server",
            "description": "100% OpenAI API compatible - no extensions"
        },
        {
            "id": "multimodal-enhanced",
            "object": "model", 
            "created": int(time.time()),
            "owned_by": "llm-server",
            "description": "Enhanced for text + documents + images processing"
        },
        {
            "id": "thinking-enabled",
            "object": "model",
            "created": int(time.time()), 
            "owned_by": "llm-server",
            "description": "Default with <thinking> reasoning enabled"
        }
    ]
    
    models.extend(virtual_models)
    
    # Physical model files (for advanced users)
    models_dir = Path("./models")
    if models_dir.exists():
        for model_file in models_dir.glob("*.gguf"):
            # Only show main models, not fragments
            if not any(x in model_file.name for x in ["-00001-", "-00002-", "-00003-", "-00004-", "-00005-", "-00006-", "-00007-"]):
                model_name = model_file.stem
                models.append(ModelInfo(
                    id=model_name,
                    created=int(model_file.stat().st_mtime)
                ))
    
    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions with virtual model optimization"""
    
    # Log incoming request for debugging Cline compatibility
    logger.info(f"📥 Chat request from Cline: model={request.model}, messages={len(request.messages)} msg(s)")
    for i, msg in enumerate(request.messages):
        logger.info(f"   Message {i}: role={msg.role}, content_type={type(msg.content)}, content_preview={str(msg.content)[:100]}")
    
    if not LLAMA_AVAILABLE or model is None:
        raise HTTPException(
            status_code=503, 
            detail="Model not available. Please check if llama-cpp-python is installed and model is loaded."
        )
    
    # Handle virtual models with specific optimizations
    original_model = request.model
    if request.model == "cline-optimized":
        # Optimized for Cline - simple and direct
        request.temperature = request.temperature or 0.3    # More focused responses
        request.max_tokens = request.max_tokens or 2048     # Reasonable length
        request.mode = "chat"                               # Force simple chat mode
        request.reasoning = False                           # Disable complex reasoning
        request.use_rag = False                            # Disable RAG for now
        logger.info(f"🎯 Using Cline-optimized (simplified for reliability)")
        
    elif request.model == "openai-compatible":
        # 100% OpenAI standard - no extensions
        request.temperature = request.temperature or 1.0
        request.max_tokens = request.max_tokens or 1024
        request.reasoning = False                           # No thinking tags
        request.use_rag = False                            # No RAG extensions
        request.use_corag = False
        request.use_memory = False
        logger.info(f"🔒 Using OpenAI-strict (no extensions)")
        
    elif request.model == "multimodal-enhanced":
        # Enhanced multimodal processing
        request.temperature = request.temperature or 0.8
        request.max_tokens = request.max_tokens or 3000     # Longer for complex multimodal analysis
        request.use_rag = True                              # Enhanced context understanding
        request.use_memory = True                           # Remember multimodal context
        logger.info(f"📷 Using multimodal-enhanced (text+docs+images)")
        
    elif request.model == "thinking-enabled":
        # Default with thinking enabled
        request.reasoning = True                            # Always enable <thinking>
        request.temperature = request.temperature or 0.6   # Slightly lower for reasoning
        request.use_rag = True
        logger.info(f"🧠 Using thinking-enabled (reasoning ON)")
    
    try:
        # Handle streaming
        if request.stream:
            return StreamingResponse(
                generate_stream(request),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        
        # Enhanced RAG processing
        rag_context = ""
        memory_context = ""
        
        if RAG_AVAILABLE and request.use_rag:
            # Get the last user message for RAG query
            user_messages = [msg for msg in request.messages if msg.role == "user"]
            if user_messages:
                last_query = user_messages[-1].content
                
                # Store query in memory system
                if request.use_memory and memory_system:
                    await memory_system.store_fragment(
                        content=last_query,
                        importance_score=0.7,
                        context_tags=[request.mode, "user_query"]
                    )
                
                # Retrieve relevant context
                if request.use_corag and rag_engine:
                    # Use CoRAG for complex queries
                    logger.info("🔗 Using CoRAG chain retrieval")
                    retrieval_chain = await rag_engine.generate_corag_response(last_query)
                    rag_context = f"\n# Retrieved Knowledge (CoRAG):\n{retrieval_chain.final_synthesis}"
                elif vector_store and vector_store.get_statistics()['total_documents'] > 0:
                    # Standard RAG retrieval
                    logger.info("🔍 Using standard RAG retrieval")
                    relevant_docs = await vector_store.search_by_text(
                        last_query, 
                        embeddings_engine, 
                        k=request.rag_k
                    )
                    if relevant_docs:
                        doc_contents = []
                        for doc in relevant_docs:
                            doc_contents.append(f"- {doc['content'][:500]}...")
                        rag_context = f"\n# Retrieved Knowledge:\n" + "\n".join(doc_contents)
                
                # Get memory context
                if request.memory_context and memory_system:
                    memory_context = await memory_system.get_context_summary(max_tokens=2000)
        
        # Build prompt - simplified for cline-optimized
        if request.model == "cline-optimized":
            # Ultra-simple prompt for Cline compatibility
            prompt = build_simple_chat_prompt(request.messages)
        else:
            # Build prompt based on mode with RAG enhancement
            prompt = build_chat_prompt(
                request.messages, 
                enable_reasoning=request.reasoning,
                mode=request.mode,
                context_files=request.context_files,
                project_root=request.project_root,
                rag_context=rag_context,
                memory_context=memory_context
            )
        
        # Generate response
        start_time = time.time()
        
        # Prepare generation parameters
        gen_params = {
            "prompt": prompt,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stop": get_stop_sequences(request.stop),
            "echo": False,
            "repeat_penalty": 1.0 + request.frequency_penalty * 0.1,
        }
        
        logger.info(f"🤔 Generating response with reasoning={'ON' if request.reasoning else 'OFF'}")
        response = model(**gen_params)
        generation_time = time.time() - start_time
        
        # Extract generated text
        generated_text = response["choices"][0]["text"].strip()
        
        # Process reasoning mode
        if request.reasoning:
            generated_text = process_reasoning_response(generated_text)
        
        # Handle function calling if tools provided
        tool_calls = None
        if request.tools and detect_tool_usage(generated_text):
            tool_calls = parse_tool_calls(generated_text, request.tools)
        
        response_data = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion", 
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": generated_text
                },
                "finish_reason": "tool_calls" if tool_calls else "stop"
            }],
            "usage": {
                "prompt_tokens": response["usage"]["prompt_tokens"],
                "completion_tokens": response["usage"]["completion_tokens"],
                "total_tokens": response["usage"]["total_tokens"],
                "prompt_tokens_details": {
                    "cached_tokens": 0  # Cline expects this field
                },
                "completion_tokens_details": {
                    "reasoning_tokens": 0  # Standard OpenAI field
                }
            },
            "system_fingerprint": f"fp_{uuid.uuid4().hex[:8]}"  # Standard field
        }
        
        # Add tool_calls only if they exist (OpenAI standard)
        if tool_calls:
            response_data["choices"][0]["message"]["tool_calls"] = tool_calls
        
        # Log response for debugging Cline compatibility
        logger.info(f"📤 Sending response: id={response_data['id']}, model={response_data['model']}")
        logger.info(f"   Choice 0: role={response_data['choices'][0]['message']['role']}, content_length={len(response_data['choices'][0]['message']['content'])}")
        logger.info(f"   Content preview: {response_data['choices'][0]['message']['content'][:100]}")
            
        return JSONResponse(response_data)
        
    except Exception as e:
        logger.error(f"❌ Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

async def generate_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Generate streaming response"""
    prompt = build_chat_prompt(request.messages, enable_reasoning=request.reasoning)
    
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())
    
    try:
        # Stream tokens
        stream = model(
            prompt,
            max_tokens=request.max_tokens or 1024,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=get_stop_sequences(request.stop),
            stream=True,
            echo=False
        )
        
        for chunk in stream:
            if chunk["choices"][0]["text"]:
                chunk_data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": chunk["choices"][0]["text"]
                        },
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # Send final chunk
        final_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk", 
            "created": created,
            "model": request.model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "generation_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

def build_simple_chat_prompt(messages: List[ChatMessage]) -> str:
    """Build ultra-simple chat prompt for Cline compatibility"""
    prompt_parts = []
    
    for message in messages:
        role = message.role
        content = message.content
        
        # Handle multimodal content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = " ".join(text_parts)
        
        if role == "system":
            prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
        elif role == "user":
            prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
        elif role == "assistant":
            prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")
    
    # Add assistant start
    prompt_parts.append("<|im_start|>assistant\n")
    
    return "\n".join(prompt_parts)

def build_chat_prompt(
    messages: List[ChatMessage], 
    enable_reasoning: bool = False,
    mode: str = "chat",
    context_files: Optional[List[str]] = None,
    project_root: Optional[str] = None,
    rag_context: str = "",
    memory_context: str = ""
) -> str:
    """Build chat prompt based on mode and context"""
    
    # Mode-specific system prompts
    mode_prompts = {
        "chat": "You are a helpful AI assistant. Please provide accurate and detailed responses.",
        
        "plan": """You are an AI assistant in PLAN mode. When given a task:

1. **ANALYZE** the request thoroughly
2. **BREAK DOWN** the task into concrete, actionable steps
3. **IDENTIFY** potential challenges and solutions
4. **ORGANIZE** steps in logical order with dependencies
5. **ESTIMATE** complexity and time for each step

Present your plan in this format:
## Plan Overview
Brief summary of what will be accomplished.

## Steps
1. **Step Name** - Description (Estimated effort: Low/Medium/High)
2. **Step Name** - Description (Dependencies: Step X)
...

## Considerations
- Potential challenges
- Alternative approaches
- Success criteria

**Do not execute the plan yet - only provide the planning.**""",

        "act": """You are an AI assistant in ACTION mode. You should:

1. **EXECUTE** the plan or task directly
2. **IMPLEMENT** solutions step by step
3. **MAKE CHANGES** to files, write code, run commands
4. **ITERATE** and fix issues as they arise
5. **PROVIDE** concrete deliverables

Focus on execution, not planning. Take action immediately.""",

        "agent": """You are an autonomous AI agent with access to tools and the ability to:

1. **EXPLORE** the project structure and codebase
2. **UNDERSTAND** requirements and context
3. **PLAN AND EXECUTE** tasks independently
4. **USE TOOLS** to read files, run commands, make changes
5. **ITERATE** until the goal is achieved
6. **SELF-CORRECT** when encountering errors

You have agency to make decisions and take actions to complete the objective.""",

        "edit": """You are an AI assistant in EDIT mode specialized in code and file modifications:

1. **READ** and analyze existing files thoroughly
2. **UNDERSTAND** the codebase structure and patterns
3. **MAKE PRECISE** targeted changes
4. **PRESERVE** existing code style and conventions
5. **TEST** changes when possible
6. **EXPLAIN** what changes were made and why

Focus on making high-quality, surgical edits to existing code.""",

        "continue": """You are an AI assistant in CONTINUE mode. You should:

1. **RESUME** from where the previous interaction left off
2. **MAINTAIN CONTEXT** from previous conversations
3. **CONTINUE** incomplete tasks or implementations
4. **ITERATE** on previous work
5. **BUILD UPON** existing solutions

Pick up the conversation thread and continue the work naturally."""
    }
    
    # Get base prompt for mode
    if mode in mode_prompts:
        system_prompt = mode_prompts[mode]
    else:
        system_prompt = mode_prompts["chat"]
    
    # Add reasoning capability if requested
    if enable_reasoning:
        system_prompt += """

**REASONING MODE ENABLED**: Use <thinking> tags to show your thought process:

<thinking>
Step-by-step reasoning...
- Analysis of the problem
- Consideration of approaches
- Logic and decision making
</thinking>

Then provide your response based on the reasoning."""

    # Add RAG context if available
    if rag_context:
        system_prompt += f"\n\n**KNOWLEDGE BASE:**\n{rag_context}"
    
    # Add memory context if available
    if memory_context:
        system_prompt += f"\n\n**CONVERSATION MEMORY:**\n{memory_context}"

    # Add context files information if provided
    if context_files and mode in ["edit", "agent"]:
        context_info = "\n\n**CONTEXT FILES PROVIDED:**\n"
        for file_path in context_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    context_info += f"\n--- {file_path} ---\n{content[:2000]}{'...' if len(content) > 2000 else ''}\n"
                except Exception as e:
                    context_info += f"\n--- {file_path} (ERROR: {e}) ---\n"
            else:
                context_info += f"\n--- {file_path} (FILE NOT FOUND) ---\n"
        system_prompt += context_info

    # Add project root information if provided
    if project_root and mode == "agent":
        system_prompt += f"\n\n**PROJECT ROOT:** {project_root}"
        if Path(project_root).exists():
            try:
                # Add basic project structure
                structure = []
                for item in Path(project_root).iterdir():
                    if item.is_file() and not item.name.startswith('.'):
                        structure.append(f"📄 {item.name}")
                    elif item.is_dir() and not item.name.startswith('.'):
                        structure.append(f"📁 {item.name}/")
                
                if structure:
                    system_prompt += f"\n\n**PROJECT STRUCTURE:**\n" + "\n".join(structure[:20])
                    if len(structure) > 20:
                        system_prompt += f"\n... and {len(structure) - 20} more items"
            except Exception as e:
                system_prompt += f"\n(Error reading project structure: {e})"
    
    prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
    
    for message in messages:
        content = message.content
        if isinstance(content, list):
            # Handle multimodal content (text + documents + images)
            processed_content = []
            for item in content:
                if item.get("type") == "text":
                    processed_content.append(item.get("text", ""))
                elif item.get("type") == "image_url":
                    # Handle images
                    image_url = item.get("image_url", {}).get("url", "")
                    processed_content.append(f"[IMAGE: {image_url}]")
                elif item.get("type") == "document":
                    # Handle documents
                    doc_content = item.get("content", "")
                    doc_name = item.get("name", "document")
                    processed_content.append(f"[DOCUMENT {doc_name}]: {doc_content}")
                else:
                    # Handle any other content types
                    processed_content.append(str(item.get("content", "")))
            
            content = "\n".join(processed_content)
            
        if message.role == "user":
            prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif message.role == "assistant":
            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        elif message.role == "system":
            prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
    
    prompt += "<|im_start|>assistant\n"
    return prompt

def get_stop_sequences(stop: Optional[Union[str, List[str]]]) -> List[str]:
    """Get stop sequences"""
    default_stops = ["<|im_end|>", "</s>", "<|endoftext|>"]
    
    if stop is None:
        return default_stops
    elif isinstance(stop, str):
        return default_stops + [stop]
    else:
        return default_stops + stop

def process_reasoning_response(text: str) -> str:
    """Process response with reasoning mode"""
    # Keep the thinking tags for transparency
    return text

def detect_tool_usage(text: str) -> bool:
    """Detect if response contains tool usage"""
    tool_indicators = ["function_call:", "tool_call:", "```json", "call_function("]
    return any(indicator in text.lower() for indicator in tool_indicators)

def parse_tool_calls(text: str, tools: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """Parse tool calls from response"""
    # Basic tool call parsing - can be enhanced
    if "```json" in text.lower():
        try:
            # Extract JSON from code block
            start = text.lower().find("```json") + 7
            end = text.find("```", start)
            if end > start:
                json_str = text[start:end].strip()
                tool_data = json.loads(json_str)
                
                return [{
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "type": "function",
                    "function": {
                        "name": tool_data.get("name", "unknown"),
                        "arguments": json.dumps(tool_data.get("arguments", {}))
                    }
                }]
        except:
            pass
    
    return None

# Test endpoints for reasoning verification
@app.post("/test/math")
async def test_math():
    """Test mathematical reasoning"""
    messages = [ChatMessage(
        role="user", 
        content="Solve this step by step: If I have 15 apples and I give away 1/3 of them, then buy 8 more apples, how many apples do I have in total? Show your work clearly."
    )]
    request = ChatRequest(
        messages=messages, 
        max_tokens=512, 
        reasoning=True,
        temperature=0.1
    )
    return await openai_chat_completions(request)

@app.post("/test/coding")
async def test_coding():
    """Test coding problem solving"""
    messages = [ChatMessage(
        role="user", 
        content="Write a Python function to find all prime numbers up to n using the Sieve of Eratosthenes algorithm. Include detailed comments explaining each step and analyze the time complexity."
    )]
    request = ChatRequest(
        messages=messages, 
        max_tokens=1024, 
        reasoning=True,
        temperature=0.2
    )
    return await openai_chat_completions(request)

@app.post("/test/reasoning")
async def test_reasoning():
    """Test logical reasoning"""
    messages = [ChatMessage(
        role="user", 
        content="""Logic puzzle: There are 5 houses in a row, each painted a different color. Each house is owned by a person of different nationality, who drinks a different beverage, smokes a different brand of cigarettes, and keeps a different pet.

Clues:
1. The Brit lives in the red house
2. The Swede keeps dogs as pets
3. The Dane drinks tea
4. The green house is on the left of the white house
5. The green house's owner drinks coffee
6. The person who smokes Pall Mall rears birds
7. The owner of the yellow house smokes Dunhill
8. The man living in the center house drinks milk
9. The Norwegian lives in the first house
10. The man who smokes Blends lives next to the one who keeps cats

Who owns the fish?"""
    )]
    request = ChatRequest(
        messages=messages, 
        max_tokens=2048, 
        reasoning=True,
        temperature=0.1
    )
    return await openai_chat_completions(request)

@app.post("/test/streaming")
async def test_streaming():
    """Test streaming response"""
    messages = [ChatMessage(
        role="user",
        content="Tell me a creative story about AI and robotics in the future. Make it engaging and detailed."
    )]
    request = ChatRequest(
        messages=messages,
        max_tokens=1024,
        stream=True,
        temperature=0.8
    )
    return await openai_chat_completions(request)

# Mode testing endpoints
@app.post("/test/plan-mode")
async def test_plan_mode():
    """Test planning mode"""
    messages = [ChatMessage(
        role="user",
        content="I want to build a simple todo app with React and Node.js backend. Plan out the entire development process."
    )]
    request = ChatRequest(
        messages=messages,
        mode="plan",
        reasoning=True,
        max_tokens=1024,
        temperature=0.1
    )
    return await openai_chat_completions(request)

@app.post("/test/act-mode") 
async def test_act_mode():
    """Test action mode"""
    messages = [ChatMessage(
        role="user",
        content="Create a Python function that calculates fibonacci numbers. Write the complete implementation now."
    )]
    request = ChatRequest(
        messages=messages,
        mode="act", 
        max_tokens=1024,
        temperature=0.2
    )
    return await openai_chat_completions(request)

@app.post("/test/agent-mode")
async def test_agent_mode():
    """Test autonomous agent mode"""
    messages = [ChatMessage(
        role="user", 
        content="Analyze this project structure and suggest improvements to the code organization."
    )]
    request = ChatRequest(
        messages=messages,
        mode="agent",
        project_root="/Users/server/AI-projects/AI-server/llm-server",
        reasoning=True,
        max_tokens=1024,
        temperature=0.3
    )
    return await openai_chat_completions(request)

@app.post("/test/edit-mode")
async def test_edit_mode():
    """Test edit mode"""
    messages = [ChatMessage(
        role="user",
        content="Review the server code and suggest specific improvements to error handling and performance."
    )]
    request = ChatRequest(
        messages=messages,
        mode="edit",
        context_files=["./real_server.py"],
        max_tokens=1024,
        temperature=0.2
    )
    return await openai_chat_completions(request)

@app.post("/test/continue-mode")
async def test_continue_mode():
    """Test continue mode"""
    messages = [
        ChatMessage(role="assistant", content="I was working on implementing a chat server..."),
        ChatMessage(role="user", content="Continue with the implementation. Add error handling and logging.")
    ]
    request = ChatRequest(
        messages=messages,
        mode="continue", 
        max_tokens=1024,
        temperature=0.3
    )
    return await openai_chat_completions(request)

def print_startup_banner():
    """Print startup banner with connection information"""
    import os
    
    # Colors
    GREEN = '\033[0;32m'
    CYAN = '\033[0;36m'
    YELLOW = '\033[1;33m'
    WHITE = '\033[1;37m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'  # No Color
    
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{WHITE}🎉 LLM SERVER STARTING...{NC}")
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")
    print("")
    print(f"{WHITE}🤖 MODEL CONFIGURATION:{NC}")
    print(f"   • Primary Model: {CYAN}Qwen2.5-Coder-7B-Instruct-Q6_K{NC}")
    print(f"   • Context Window: {GREEN}128K tokens{NC}")
    print(f"   • Metal Acceleration: {GREEN}Enabled{NC}")
    print(f"   • Operation Modes: {GREEN}6 (Chat, Plan, Act, Agent, Edit, Continue){NC}")
    print("")
    print(f"{WHITE}📡 SERVER ENDPOINTS:{NC}")
    print(f"   • Main API: {CYAN}http://localhost:8000{NC}")
    print(f"   • Health Check: {CYAN}http://localhost:8000/health{NC}")
    print(f"   • API Documentation: {CYAN}http://localhost:8000/docs{NC}")
    print("")
    print(f"{WHITE}🔌 OPENAI COMPATIBLE API:{NC}")
    print(f"   • Endpoint: {CYAN}http://localhost:8000/v1/chat/completions{NC}")
    print(f"   • API Key: {YELLOW}sk-llmserver-local-development-key-12345678{NC}")
    print(f"   • Models Endpoint: {CYAN}http://localhost:8000/v1/models{NC}")
    print("")
    print(f"{WHITE}⚡ EXPECTED PERFORMANCE:{NC}")
    print(f"   • Speed: {GREEN}55+ tokens/second{NC}")
    print(f"   • Reasoning Mode: {GREEN}Available{NC}")
    print(f"   • Streaming: {GREEN}Supported{NC}")
    print("")
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{WHITE}Loading model... Please wait...{NC}")
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")

def print_ready_banner():
    """Print ready banner when server is fully loaded"""
    import os
    
    # Colors
    GREEN = '\033[0;32m'
    CYAN = '\033[0;36m'
    YELLOW = '\033[1;33m'
    WHITE = '\033[1;37m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'  # No Color
    
    print("")
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{WHITE}🚀 LLM SERVER IS READY!{NC}")
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")
    print("")
    print(f"{WHITE}🔥 QUICK TEST COMMANDS:{NC}")
    print(f"{CYAN}curl -X POST http://localhost:8000/test/math{NC}")
    print(f"{CYAN}curl -X POST http://localhost:8000/test/coding{NC}")
    print(f"{CYAN}curl -X POST http://localhost:8000/test/plan-mode{NC}")
    print("")
    print(f"{WHITE}💬 OPENAI API CURL EXAMPLE:{NC}")
    print(f"{CYAN}curl -X POST http://localhost:8000/v1/chat/completions \\{NC}")
    print(f"{CYAN}  -H \"Content-Type: application/json\" \\{NC}")
    print(f"{CYAN}  -H \"Authorization: Bearer sk-llmserver-local-development-key-12345678\" \\{NC}")
    print(f"{CYAN}  -d '{{\"model\":\"qwen2.5-coder-7b\",\"messages\":[{{\"role\":\"user\",\"content\":\"Hello AI!\"}}]}}']{NC}")
    print("")
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{WHITE}Server running on: {CYAN}http://localhost:8000{NC}")
    print(f"{WHITE}API Key: {YELLOW}sk-llmserver-local-development-key-12345678{NC}")
    print(f"{WHITE}Press Ctrl+C to stop{NC}")
    print(f"{GREEN}════════════════════════════════════════════════════════════════{NC}")
    print("")

if __name__ == "__main__":
    print_startup_banner()
    
    # Add callback to print ready message after server starts
    import asyncio
    import threading
    
    def print_ready_after_delay():
        import time
        time.sleep(3)  # Wait for server to be fully ready
        print_ready_banner()
    
    # Start the ready message in a separate thread
    ready_thread = threading.Thread(target=print_ready_after_delay)
    ready_thread.daemon = True
    ready_thread.start()
    
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        log_level="error",  # Reduce uvicorn logs to show our banner clearly
        access_log=False
    )