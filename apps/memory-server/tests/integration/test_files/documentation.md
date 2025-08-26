
# Memory-Server Documentation

## Overview
Memory-Server is a next-generation RAG system that incorporates state-of-the-art 2025 techniques:

- **LazyGraphRAG**: Zero-cost graph indexing with 1000x cost reduction
- **Late Chunking**: Context-preserving embeddings before chunking
- **Hybrid Retrieval**: Vector + Graph fusion for optimal results
- **Agentic RAG**: Multi-turn reasoning capabilities

## Quick Start

1. Install dependencies
2. Configure your API keys
3. Start the server
4. Begin ingesting documents

## API Endpoints

### Document Upload
```bash
curl -X POST "http://localhost:8001/api/v1/documents/upload"   -F "file=@document.pdf"   -F "workspace=research"
```

### Web Scraping
```bash
curl -X POST "http://localhost:8001/api/v1/documents/scrape-web"   -H "Content-Type: application/json"   -d '{"url": "https://example.com", "workspace": "research"}'
```
