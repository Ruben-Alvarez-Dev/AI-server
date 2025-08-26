# MCP Servers - Model Context Protocol Integration

## 📋 Visión General

**MCP Servers** son implementaciones del Model Context Protocol de Anthropic que exponen las capacidades avanzadas de AI-Server (Memory-Server RAG, LLM-Server, etc.) como herramientas utilizables por Claude Desktop y otros clientes MCP compatibles.

### **Composición Técnica**
- **Lenguaje**: TypeScript 5.3+ con Node.js 20+
- **Protocol**: MCP (Model Context Protocol) v1.0
- **Transport**: stdio (Standard Input/Output)
- **Validation**: Zod schemas para type safety
- **HTTP Client**: Axios para Memory-Server API calls

### **Propósito de Diseño**
Crear una interfaz estándar que permita a Claude Desktop y otros AI clients acceder directamente a las capacidades avanzadas de AI-Server sin configuración compleja, manteniendo type safety y error handling robusto.

## 🏗️ Arquitectura MCP

### **Protocol Overview**
```typescript
// MCP Server Implementation
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server(
  { name: 'memory-server-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);
```

### **Core Components**

#### **1. Memory-Server MCP (`memory-server-mcp`)**

**Configuration:**
```typescript
const MEMORY_SERVER_BASE_URL = process.env.MEMORY_SERVER_URL || 'http://localhost:8001';
const API_VERSION = 'v1';
const BASE_API_URL = `${MEMORY_SERVER_BASE_URL}/api/${API_VERSION}`;
```

**Available Tools:**

##### **Document Search & Retrieval**
```typescript
const SearchSchema = z.object({
  query: z.string().describe('Search query'),
  workspace: z.string().optional().describe('Workspace (code, research, projects, personal)'),
  limit: z.number().default(10).describe('Maximum results'),
  semantic: z.boolean().default(true).describe('Enable semantic search')
});

// Implementation
async function handleSearch(query: string, workspace?: string): Promise<CallToolResult> {
  const response = await axios.get(`${BASE_API_URL}/documents/search`, {
    params: { query, workspace, limit, semantic: true }
  });
  
  return {
    content: [{
      type: "text",
      text: `Found ${response.data.results.length} results:\\n\\n${formatSearchResults(response.data.results)}`
    }]
  };
}
```

##### **Document Upload & Ingestion**
```typescript
const DocumentUploadSchema = z.object({
  content: z.string().describe('Document content'),
  filename: z.string().describe('Original filename'),
  workspace: z.string().default('research').describe('Target workspace'),
  auto_summarize: z.boolean().default(true).describe('Generate summary'),
  tags: z.string().optional().describe('Comma-separated tags')
});

// LazyGraphRAG integration automática
async function handleDocumentUpload(params: DocumentUploadParams): Promise<CallToolResult> {
  const formData = new FormData();
  formData.append('file', new Blob([params.content]), params.filename);
  formData.append('workspace', params.workspace);
  formData.append('auto_summarize', params.auto_summarize.toString());
  
  if (params.tags) {
    formData.append('tags', params.tags);
  }
  
  const response = await axios.post(`${BASE_API_URL}/documents/upload`, formData);
  return formatUploadResponse(response.data);
}
```

##### **Web Scraping & Research**
```typescript
const WebScrapeSchema = z.object({
  url: z.string().url().describe('URL to scrape'),
  workspace: z.string().default('research').describe('Target workspace'),
  max_pages: z.number().default(1).describe('Maximum pages'),
  include_pdfs: z.boolean().default(false).describe('Include PDFs'),
  include_external: z.boolean().default(false).describe('Include external links')
});

// Integration con Web Scraper tool
async function handleWebScrape(params: WebScrapeParams): Promise<CallToolResult> {
  const response = await axios.post(`${BASE_API_URL}/web/scrape`, {
    url: params.url,
    workspace: params.workspace,
    options: {
      max_pages: params.max_pages,
      include_pdfs: params.include_pdfs,
      include_external: params.include_external
    }
  });
  
  return {
    content: [{
      type: "text", 
      text: `Successfully scraped ${response.data.pages_processed} pages from ${params.url}`
    }]
  };
}
```

##### **Advanced Summarization**
```typescript
const SummarizeContentSchema = z.object({
  content: z.string().describe('Content to summarize'),
  summary_type: z.enum([
    'extractive',     // Key sentences extraction
    'abstractive',    // AI-generated summary
    'structured',     // Organized sections
    'bullet_points',  // Key points list
    'technical',      // Technical documentation
    'narrative'       // Story-like summary
  ]).default('extractive'),
  max_length: z.number().optional().describe('Max length in words'),
  workspace: z.string().default('research').describe('Context workspace')
});

async function handleSummarization(params: SummarizeParams): Promise<CallToolResult> {
  const response = await axios.post(`${BASE_API_URL}/summarize/content`, {
    content: params.content,
    summary_type: params.summary_type,
    max_length: params.max_length,
    workspace: params.workspace
  });
  
  return {
    content: [{
      type: "text",
      text: `## ${params.summary_type.toUpperCase()} Summary\\n\\n${response.data.summary}`
    }]
  };
}
```

##### **Intelligent Web Search**
```typescript
const WebSearchSchema = z.object({
  query: z.string().describe('Search query'),
  num_results: z.number().default(5).describe('Number of results'),
  search_type: z.enum(['search', 'documentation', 'code', 'forums']).default('search'),
  language: z.string().optional().describe('Programming language for code search'),
  forum: z.string().optional().describe('Specific forum for forum search'),
  workspace: z.string().default('research').describe('Target workspace'),
  auto_ingest: z.boolean().default(false).describe('Auto-ingest results')
});

// Multi-type search capability
async function handleWebSearch(params: WebSearchParams): Promise<CallToolResult> {
  const searchEndpoint = getSearchEndpoint(params.search_type);
  const response = await axios.post(`${BASE_API_URL}/web/${searchEndpoint}`, {
    query: params.query,
    options: {
      num_results: params.num_results,
      language: params.language,
      forum: params.forum,
      auto_ingest: params.auto_ingest,
      workspace: params.workspace
    }
  });
  
  return formatSearchResponse(response.data, params.search_type);
}
```

##### **Activity Tracking Integration**
```typescript
const ActivityTrackingSchema = z.object({
  events: z.array(z.record(z.any())).describe('Activity events'),
  workspace: z.string().default('code').describe('Target workspace'),
  source: z.string().default('mcp-client').describe('Source identifier'),
  auto_tag: z.boolean().default(true).describe('Enable auto-tagging')
});

// Integration con VSCode Activity Tracker
async function handleActivityTracking(params: ActivityParams): Promise<CallToolResult> {
  const response = await axios.post(`${BASE_API_URL}/documents/activity`, {
    workspace: params.workspace,
    events: params.events,
    source: params.source,
    auto_tag: params.auto_tag,
    metadata: {
      mcp_server: 'memory-server-mcp',
      client_type: 'claude-desktop',
      timestamp: new Date().toISOString()
    }
  });
  
  return {
    content: [{
      type: "text",
      text: `Tracked ${params.events.length} activity events to ${params.workspace} workspace`
    }]
  };
}
```

## 🔗 Integration Architecture

### **MCP Protocol Flow**
```
Claude Desktop → MCP Server → Memory-Server API → LazyGraphRAG → Response
                     ↓
                ATLAS Logging (automatic audit trail)
```

### **Tool Registration System**
```typescript
const tools: Tool[] = [
  {
    name: 'memory_search',
    description: 'Search documents using advanced RAG with LazyGraphRAG',
    inputSchema: SearchSchema
  },
  {
    name: 'document_upload',
    description: 'Upload and process documents with Late Chunking',
    inputSchema: DocumentUploadSchema
  },
  {
    name: 'web_scrape',
    description: 'Scrape web content and ingest into Memory-Server',
    inputSchema: WebScrapeSchema
  },
  {
    name: 'web_search',
    description: 'Intelligent web search with auto-ingestion',
    inputSchema: WebSearchSchema
  },
  {
    name: 'summarize_content',
    description: 'Generate intelligent summaries with multiple types',
    inputSchema: SummarizeContentSchema
  },
  {
    name: 'track_activity',
    description: 'Track development activity for enhanced context',
    inputSchema: ActivityTrackingSchema
  }
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: tools
}));
```

### **Error Handling & Resilience**
```typescript
async function safeApiCall<T>(apiCall: () => Promise<T>, toolName: string): Promise<CallToolResult> {
  try {
    const result = await apiCall();
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    // Log to ATLAS for debugging
    console.error(`MCP Tool Error [${toolName}]:`, errorMessage);
    
    return {
      content: [{
        type: "text",
        text: `❌ Error in ${toolName}: ${errorMessage}\\n\\nPlease check Memory-Server is running on ${MEMORY_SERVER_BASE_URL}`
      }],
      isError: true
    };
  }
}
```

## 🚀 Installation & Configuration

### **Setup Process**
```bash
cd tools/mcp-servers/memory-server-mcp/

# Install dependencies
npm install

# Build TypeScript
npm run build

# Test locally
npm run dev
```

### **Claude Desktop Integration**
```json
// ~/.config/claude-desktop/claude_desktop_config.json
{
  "mcpServers": {
    "memory-server": {
      "command": "node",
      "args": ["/path/to/AI-server/tools/mcp-servers/memory-server-mcp/dist/index.js"],
      "env": {
        "MEMORY_SERVER_URL": "http://localhost:8001"
      }
    }
  }
}
```

### **Environment Configuration**
```bash
# Required environment variables
export MEMORY_SERVER_URL="http://localhost:8001"

# Optional configuration
export MCP_LOG_LEVEL="info"
export MCP_TIMEOUT="30000"  # 30 second timeout
```

## 🎯 Usage Examples

### **Research Workflow con Claude Desktop**

```
Human: Search for existing authentication implementations in our codebase

Claude: I'll search your Memory-Server for authentication implementations.

[Uses memory_search tool]
🔍 Found 5 results:
1. JWT Authentication Middleware (apps/llm-server/auth.py)
2. OAuth2 Implementation Guide (docs/auth/oauth2.md) 
3. FastAPI Authentication Pattern (examples/fastapi-auth.py)
...