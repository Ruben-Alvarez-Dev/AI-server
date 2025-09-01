# Chapter 5: LLM Infrastructure
**30 tasks | Phase 3 | Prerequisites: Chapter 4 completed**

## 5.1 llama.cpp Compilation (9 tasks)

- [ ] **5.1.1 Clone llama.cpp repository**  
  Clone the official llama.cpp repository from GitHub, checking out a stable release tag rather than main branch. This ensures consistent behavior and avoids breaking changes. Document the specific version used for reproducibility.

- [ ] **5.1.2 Checkout stable version**  
  Switch to a tested stable version tag like b2600 that's known to work well with our model set. Stable versions have fewer bugs and better performance. Keep a local fork in case upstream changes break compatibility.

- [ ] **5.1.3 Apply Metal optimizations patches**  
  Apply any custom patches for improved Metal performance on Apple Silicon, if available from community. These optimizations can significantly improve inference speed. Document all modifications for future updates.

- [ ] **5.1.4 Compile with LLAMA_METAL=on**  
  Build with make LLAMA_METAL=1 to enable Metal GPU acceleration, essential for acceptable performance. Metal support offloads computation to GPU/Neural Engine. Verify Metal kernels compile without errors.

- [ ] **5.1.5 Compile with LLAMA_ACCELERATE=on**  
  Include LLAMA_ACCELERATE=1 to use Apple's Accelerate framework for optimized BLAS operations. This framework provides CPU optimizations for matrix operations. The combination with Metal maximizes performance.

- [ ] **5.1.6 Enable Flash Attention v2**  
  Compile with Flash Attention support for improved memory efficiency and speed on long contexts. This optimization reduces memory bandwidth requirements. Verify it works with our context sizes.

- [ ] **5.1.7 Build server component**  
  Build the server component using make server to get the HTTP API server for model serving. The server provides a clean interface for model interaction. Configure for production use with proper timeouts.

- [ ] **5.1.8 Run benchmark tests**  
  Execute llama.cpp benchmark suite to verify performance meets expectations on your hardware. Record baseline metrics for each quantization level. These benchmarks help identify performance regressions.

- [ ] **5.1.9 Verify Metal GPU utilization**  
  Use Activity Monitor or powermetrics to confirm GPU is being utilized during inference. GPU usage should spike during generation. Document expected utilization patterns for monitoring.

## 5.2 Memory Server Models (10 tasks)

- [ ] **5.2.1 Download Qwen2.5-Coder-7B-Instruct GGUF**  
  Download the instruction-tuned coding model from HuggingFace, choosing the official GGUF conversion. This model serves as the primary code analysis engine. Verify checksum matches published values.

- [ ] **5.2.2 Quantize to Q6_K format**  
  Quantize using ./quantize model.gguf model-q6_k.gguf Q6_K for optimal quality/size trade-off. Q6_K maintains high quality while reducing size by ~40%. Test output quality remains acceptable.

- [ ] **5.2.3 Download Nomic-Embed-Text-v1.5**  
  Obtain the Nomic embedding model, one of the best open-source text encoders available. This model generates embeddings for RAG operations. Choose the GGUF format for consistency.

- [ ] **5.2.4 Convert to F16 format**  
  Keep embeddings model in F16 precision for maximum quality since it's small enough. Full precision ensures best embedding quality. The size difference is minimal for this model.

- [ ] **5.2.5 Download Phi-3-Mini-128K-Instruct**  
  Download Microsoft's Phi-3 with massive 128K context for document summarization tasks. This model handles large document processing. The long context is crucial for comprehensive summaries.

- [ ] **5.2.6 Quantize to Q5_K_M format**  
  Use Q5_K_M quantization to balance quality with the model's memory requirements. This format maintains good performance while fitting in allocated RAM. Test summarization quality remains high.

- [ ] **5.2.7 Download DeepSeek-Coder-1.3B**  
  Get the small, fast DeepSeek model for quick code analysis and syntax operations. This model provides rapid responses for simple tasks. Its speed makes it ideal for real-time operations.

- [ ] **5.2.8 Quantize to Q8_0 format**  
  Use minimal quantization (Q8_0) since the model is already small, preserving maximum quality. Higher precision is affordable for small models. This ensures best performance for code tasks.

- [ ] **5.2.9 Download Qwen2-VL-7B-Instruct**  
  Obtain Qwen's vision-language model for processing screenshots and diagrams. This multimodal model enables visual understanding. Essential for comprehensive development assistance.

- [ ] **5.2.10 Quantize to Q5_K_M format**  
  Quantize the vision model to Q5_K_M to fit within memory constraints while maintaining visual understanding. Balance is critical for multimodal models. Test image understanding capabilities post-quantization.

## 5.3 Shared Embeddings Models (3 tasks)

- [ ] **5.3.1 Download BGE-M3 embeddings model**  
  Download Beijing Academy's multilingual embedding model for cross-language code search. This model handles multiple programming languages. Provides excellent multilingual representations.

- [ ] **5.3.2 Download E5-Large-v2 embeddings model**  
  Obtain Microsoft's E5 model for high-quality semantic embeddings. This model excels at semantic similarity. Complements BGE-M3 for comprehensive coverage.

- [ ] **5.3.3 Convert both to F16 format**  
  Keep both embedding models in F16 format for optimal quality since they're relatively small. Embedding quality directly impacts retrieval accuracy. The memory cost is justified by improved search results.

## 5.4 DEV Profile Models (9 tasks)

- [ ] **5.4.1 Download Qwen2.5-0.5B (router)**  
  Get the tiny router model for rapid request classification with minimal latency. This model determines routing in <15ms. Its small size enables instant responses.

- [ ] **5.4.2 Download Qwen2.5-Coder-32B (architect)**  
  Download the large architecture model, the crown jewel for complex system design tasks. This model rivals proprietary solutions in capability. Critical for high-quality architecture decisions.

- [ ] **5.4.3 Download DeepSeek-V3 (planner)**  
  Obtain DeepSeek's latest model for task decomposition and planning operations. Excels at breaking down complex problems. The MoE architecture provides efficiency.

- [ ] **5.4.4 Download CodeGemma-7B (worker)**  
  Get Google's CodeGemma for specialized code generation tasks. Trained on high-quality code datasets. Provides clean, well-structured code output.

- [ ] **5.4.5 Download Starcoder2-7B (worker)**  
  Download BigCode's Starcoder2 for additional code generation capacity. Trained on permissively licensed code. Complements CodeGemma with different strengths.

- [ ] **5.4.6 Download DeepSeek-Coder-6.7B (worker)**  
  Obtain DeepSeek's specialized coding model for algorithm implementation. Excellent at algorithmic problems. Provides diversity in the worker pool.

- [ ] **5.4.7 Download Llama-3.2-3B (worker)**  
  Get Meta's small, fast model for quick utility functions and simple tasks. Handles basic operations rapidly. Useful for non-critical path work.

- [ ] **5.4.8 Download Phi-3.5-MoE (QA)**  
  Download Microsoft's MoE model for quality assurance and testing tasks. Excels at finding bugs and issues. The MoE architecture activates relevant experts.

- [ ] **5.4.9 Quantize all to specified formats**  
  Quantize each model according to specifications: IQ4_XS for 32B models, Q5_K_M for 7B models, Q8_0 for small models. These formats balance quality with memory constraints. Test each model post-quantization.

## 5.5 Model Verification (5 tasks)

- [ ] **5.5.1 Test each model loads correctly**  
  Load each model using llama.cpp and verify successful initialization without errors. Check for missing files or corruption. Document load times for operational planning.

- [ ] **5.5.2 Verify quantization quality**  
  Run standard prompts through each quantized model and compare outputs to original where possible. Ensure quality degradation is acceptable. Document any noticeable quality issues.

- [ ] **5.5.3 Check memory usage per model**  
  Monitor actual RAM usage when each model is loaded to verify it matches expectations. Account for KV cache and overhead. This data informs resource planning.

- [ ] **5.5.4 Benchmark inference speed**  
  Measure tokens per second for each model at different context sizes. Create performance baseline for monitoring. These metrics guide batch size and timeout configurations.

- [ ] **5.5.5 Test context window limits**  
  Verify each model handles its advertised context size without errors or quality degradation. Test with maximum context to find practical limits. Document actual vs theoretical context limits.

## Progress Summary
- **Total Tasks**: 30
- **Completed**: 0/30
- **Current Section**: 5.1 llama.cpp Compilation
- **Next Checkpoint**: 5.1.1