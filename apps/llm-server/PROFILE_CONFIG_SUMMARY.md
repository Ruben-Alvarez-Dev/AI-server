# Profile-Based Model Selection Configuration

## Overview
Successfully configured automatic profile-based model selection for LLM-Server that intelligently chooses between Qwen-Coder (DEV profile) and Qwen-Instruct (GENERAL profile) based on query context.

## Downloaded Models
- ✅ **Qwen2.5-Coder-7B-Instruct-Q6_K.gguf** (4.73 GB) - DEV/CODE profile
- ✅ **Qwen2.5-7B-Instruct-Q6_K.gguf** (5.47 GB) - GENERAL/CHAT profile

Both models use optimized Q6_K quantization for best performance/size ratio on Apple Silicon with llama.cpp.

## Profile Configuration

### Available Profiles
- **DEV**: Development/coding queries → Qwen2.5-Coder-7B-Instruct
- **GENERAL**: General conversation → Qwen2.5-7B-Instruct  
- **CODE**: Explicit code requests → Qwen2.5-Coder-7B-Instruct
- **CHAT**: Chat/conversation → Qwen2.5-7B-Instruct
- **DEFAULT**: Fallback → Qwen2.5-7B-Instruct

### Auto-Detection Logic
The system automatically detects DEV profile for queries containing:
- Code keywords: `function`, `class`, `import`, `def`, `var`, `const`, `let`
- Control structures: `if (`, `for (`, `while (`, `try {`, `catch`, `return`
- Development terms: `debug`, `error`, `exception`, `api`, `endpoint`, `http`
- Database terms: `database`, `sql`, `query`, `model`, `controller`, `service`
- File extensions: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.php`

All other queries default to GENERAL profile.

## Usage Examples

### Manual Profile Selection
```python
# Force DEV profile
dev_llama = OptimizedLlama(profile="DEV", auto_detect_profile=False)

# Force GENERAL profile  
general_llama = OptimizedLlama(profile="GENERAL", auto_detect_profile=False)
```

### Automatic Profile Detection
```python
# Enable auto-detection (default)
auto_llama = OptimizedLlama(profile="GENERAL", auto_detect_profile=True)

# Query: "How do I fix this Python function?" → Auto-switches to DEV
# Query: "What's the weather like?" → Stays on GENERAL
```

### Model Pool with Profiles
```python
# Get model with profile
model = await MODEL_POOL.get_model(
    model_id="llm_main",
    profile="DEV", 
    auto_detect_profile=True
)
```

## Test Results
✅ Profile auto-detection: 8/8 test cases passed
✅ Model selection by profile: All profiles working  
✅ OptimizedLlama creation: Configuration successful
✅ Model info: Profile data included

## Configuration Files Modified
- `/configs/llama_cpp/m1_ultra_config.py`: Added profile-based model mapping
- `/configs/llama_cpp/optimized_llama.py`: Added auto-detection and switching logic

## Next Steps
The profile-based model selection is now ready for use in:
1. RAG service endpoints (8911-8914) 
2. Memory-Server HTTP calls to LLM-Server
3. Manual model selection via API

The system will automatically choose the optimal model based on query context while maintaining the option for explicit profile selection when needed.