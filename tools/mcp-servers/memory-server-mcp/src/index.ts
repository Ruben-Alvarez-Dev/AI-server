#!/usr/bin/env node

/**
 * Memory-Server MCP Server
 * 
 * Provides MCP (Model Context Protocol) interface to Memory-Server's
 * advanced RAG capabilities including LazyGraphRAG, Late Chunking,
 * and intelligent workspace management.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
  CallToolResult,
  TextContent,
  ImageContent,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import { z } from 'zod';

// Configuration
const MEMORY_SERVER_BASE_URL = process.env.MEMORY_SERVER_URL || 'http://localhost:8001';
const API_VERSION = 'v1';
const BASE_API_URL = `${MEMORY_SERVER_BASE_URL}/api/${API_VERSION}`;

// Zod schemas for validation
const SearchSchema = z.object({
  query: z.string().describe('Search query'),
  workspace: z.string().optional().describe('Workspace to search in (code, research, projects, personal)'),
  limit: z.number().default(10).describe('Maximum number of results'),
  semantic: z.boolean().default(true).describe('Enable semantic search')
});

const DocumentUploadSchema = z.object({
  content: z.string().describe('Document content to upload'),
  filename: z.string().describe('Original filename'),
  workspace: z.string().default('research').describe('Target workspace'),
  auto_summarize: z.boolean().default(true).describe('Generate automatic summary'),
  tags: z.string().optional().describe('Comma-separated tags')
});

const WebScrapeSchema = z.object({
  url: z.string().url().describe('URL to scrape'),
  workspace: z.string().default('research').describe('Target workspace'),
  max_pages: z.number().default(1).describe('Maximum pages to scrape'),
  include_pdfs: z.boolean().default(false).describe('Include PDF content'),
  include_external: z.boolean().default(false).describe('Include external links')
});

const WebSearchSchema = z.object({
  query: z.string().describe('Search query'),
  num_results: z.number().default(5).describe('Number of results'),
  search_type: z.enum(['search', 'documentation', 'code', 'forums']).default('search').describe('Type of search'),
  language: z.string().optional().describe('Programming language filter for code search'),
  forum: z.string().optional().describe('Specific forum for forum search'),
  workspace: z.string().default('research').describe('Target workspace'),
  auto_ingest: z.boolean().default(false).describe('Automatically ingest results')
});

const ActivityTrackingSchema = z.object({
  events: z.array(z.record(z.any())).describe('Array of activity events'),
  workspace: z.string().default('code').describe('Target workspace'),
  source: z.string().default('mcp-client').describe('Source of activity data'),
  auto_tag: z.boolean().default(true).describe('Enable auto-tagging')
});

// MCP Server implementation
class MemoryServerMCP {
  private server: Server;
  
  constructor() {
    this.server = new Server(
      {
        name: 'memory-server-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_memory',
            description: 'Search documents in Memory-Server using advanced RAG with LazyGraphRAG',
            inputSchema: SearchSchema,
          },
          {
            name: 'upload_document',
            description: 'Upload and process a document into Memory-Server with intelligent auto-tagging',
            inputSchema: DocumentUploadSchema,
          },
          {
            name: 'scrape_web',
            description: 'Scrape web content and ingest into Memory-Server with advanced content extraction',
            inputSchema: WebScrapeSchema,
          },
          {
            name: 'search_web',
            description: 'Search web using Serper/Firecrawl APIs with specialized search types',
            inputSchema: WebSearchSchema,
          },
          {
            name: 'track_activity',
            description: 'Track development activity events for contextual AI assistance',
            inputSchema: ActivityTrackingSchema,
          },
          {
            name: 'list_workspaces',
            description: 'List all available workspaces and their document counts',
            inputSchema: z.object({}),
          },
          {
            name: 'get_stats',
            description: 'Get Memory-Server processing statistics and performance metrics',
            inputSchema: z.object({}),
          }
        ] satisfies Tool[],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'search_memory':
            return await this.searchMemory(SearchSchema.parse(args));
          
          case 'upload_document':
            return await this.uploadDocument(DocumentUploadSchema.parse(args));
          
          case 'scrape_web':
            return await this.scrapeWeb(WebScrapeSchema.parse(args));
          
          case 'search_web':
            return await this.searchWeb(WebSearchSchema.parse(args));
          
          case 'track_activity':
            return await this.trackActivity(ActivityTrackingSchema.parse(args));
          
          case 'list_workspaces':
            return await this.listWorkspaces();
          
          case 'get_stats':
            return await this.getStats();
          
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error executing tool ${name}:`, error);
        return {
          content: [
            {
              type: 'text',
              text: `Error executing ${name}: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  private async searchMemory(params: z.infer<typeof SearchSchema>): Promise<CallToolResult> {
    try {
      const response = await axios.get(`${BASE_API_URL}/documents/search`, {
        params: {
          query: params.query,
          workspace: params.workspace,
          limit: params.limit,
          semantic: params.semantic
        }
      });

      const results = response.data;
      
      return {
        content: [
          {
            type: 'text',
            text: `# Memory-Server Search Results

**Query**: ${params.query}
**Workspace**: ${params.workspace || 'all'}
**Results Found**: ${results.results?.length || 0}

## Results:
${results.results?.map((result: any, idx: number) => `
${idx + 1}. **${result.title || 'Document'}**
   - Score: ${result.score || 'N/A'}
   - Workspace: ${result.workspace || 'Unknown'}
   - Summary: ${result.summary || result.content?.substring(0, 200) + '...' || 'No preview available'}
`).join('\n') || 'No results found.'}

*Search powered by LazyGraphRAG and Late Chunking for enhanced accuracy*`,
          },
        ] satisfies TextContent[],
      };
    } catch (error) {
      throw new Error(`Memory search failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async uploadDocument(params: z.infer<typeof DocumentUploadSchema>): Promise<CallToolResult> {
    try {
      // Create form data for file upload simulation
      const formData = new FormData();
      const blob = new Blob([params.content], { type: 'text/plain' });
      formData.append('file', blob, params.filename);
      formData.append('workspace', params.workspace);
      formData.append('auto_summarize', params.auto_summarize.toString());
      if (params.tags) {
        formData.append('tags', params.tags);
      }

      const response = await axios.post(`${BASE_API_URL}/documents/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = response.data;

      return {
        content: [
          {
            type: 'text',
            text: `# Document Upload Successful ✅

**Document ID**: ${result.document_id}
**Filename**: ${params.filename}
**Workspace**: ${result.workspace}
**Status**: ${result.processing_status}
**Auto-tags Applied**: ${result.metadata?.auto_tags?.join(', ') || 'None'}

${result.message}

*Document processed with intelligent auto-tagging and workspace classification*`,
          },
        ] satisfies TextContent[],
      };
    } catch (error) {
      throw new Error(`Document upload failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async scrapeWeb(params: z.infer<typeof WebScrapeSchema>): Promise<CallToolResult> {
    try {
      const response = await axios.post(`${BASE_API_URL}/documents/scrape-web`, {
        url: params.url,
        workspace: params.workspace,
        max_pages: params.max_pages,
        include_pdfs: params.include_pdfs,
        include_external: params.include_external
      });

      const result = response.data;

      return {
        content: [
          {
            type: 'text',
            text: `# Web Scraping Completed ✅

**URL**: ${result.url}
**Pages Scraped**: ${result.pages_scraped}
**Document ID**: ${result.document_id}
**Workspace**: ${result.workspace}

${result.message}

*Content extracted using advanced Playwright automation and processed with intelligent content analysis*`,
          },
        ] satisfies TextContent[],
      };
    } catch (error) {
      throw new Error(`Web scraping failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async searchWeb(params: z.infer<typeof WebSearchSchema>): Promise<CallToolResult> {
    try {
      const endpoint = params.search_type === 'search' ? 'web' : params.search_type;
      const response = await axios.post(`${BASE_API_URL}/search/${endpoint}`, {
        query: params.query,
        topic: params.query, // For documentation/code/forums endpoints
        num_results: params.num_results,
        language: params.language,
        forum: params.forum,
        workspace: params.workspace,
        auto_ingest: params.auto_ingest
      });

      const result = response.data;
      const results = result.results || result.documents || result.examples || result.discussions || [];

      return {
        content: [
          {
            type: 'text',
            text: `# Web Search Results (${params.search_type})

**Query**: ${params.query}
**Results Found**: ${results.length}
**Auto-Ingested**: ${params.auto_ingest ? 'Yes' : 'No'}

## Results:
${results.map((item: any, idx: number) => `
${idx + 1}. **${item.title}**
   - URL: ${item.url}
   - Snippet: ${item.snippet || item.content?.substring(0, 150) + '...' || 'No preview'}
   ${item.language ? `- Language: ${item.language}` : ''}
`).join('\n')}

*Search powered by Serper API and Firecrawl for enhanced content extraction*`,
          },
        ] satisfies TextContent[],
      };
    } catch (error) {
      throw new Error(`Web search failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async trackActivity(params: z.infer<typeof ActivityTrackingSchema>): Promise<CallToolResult> {
    try {
      const response = await axios.post(`${BASE_API_URL}/documents/activity`, {
        workspace: params.workspace,
        events: params.events,
        source: params.source,
        auto_tag: params.auto_tag,
        metadata: {
          mcp_client: true,
          timestamp: new Date().toISOString()
        }
      });

      const result = response.data;

      return {
        content: [
          {
            type: 'text',
            text: `# Activity Tracking Completed ✅

**Events Processed**: ${result.events_processed}
**Workspace**: ${result.workspace}
**Document ID**: ${result.document_id}
**Processing Time**: ${result.processing_time}s

${result.message}

*Activity data processed with intelligent auto-tagging for enhanced contextual AI assistance*`,
          },
        ] satisfies TextContent[],
      };
    } catch (error) {
      throw new Error(`Activity tracking failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async listWorkspaces(): Promise<CallToolResult> {
    try {
      const response = await axios.get(`${BASE_API_URL}/documents/workspaces`);
      const result = response.data;

      return {
        content: [
          {
            type: 'text',
            text: `# Memory-Server Workspaces

**Active Workspace**: ${result.active_workspace}
**Total Workspaces**: ${result.workspaces.length}

## Workspaces:
${result.workspaces.map((workspace: string) => `
- **${workspace}**: ${result.total_documents[workspace] || 0} documents
  ${workspace === result.active_workspace ? '(Currently Active)' : ''}`).join('\n')}

*Workspaces provide organized content silos for different project contexts*`,
          },
        ] satisfies TextContent[],
      };
    } catch (error) {
      throw new Error(`Failed to list workspaces: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async getStats(): Promise<CallToolResult> {
    try {
      const response = await axios.get(`${BASE_API_URL}/documents/stats`);
      const stats = response.data;

      return {
        content: [
          {
            type: 'text',
            text: `# Memory-Server Statistics

## Processing Stats
- **Documents Processed**: ${stats.documents_processed || 0}
- **Total Chunks Created**: ${stats.total_chunks_created || 0}
- **Average Processing Time**: ${stats.avg_processing_time || 0}s
- **Total Processing Time**: ${stats.total_processing_time || 0}s
- **Errors**: ${stats.errors || 0}

## System Health
- **Last Processed**: ${stats.last_processed || 'Never'}
- **Success Rate**: ${stats.documents_processed ? ((stats.documents_processed / (stats.documents_processed + stats.errors)) * 100).toFixed(1) : 0}%

*Statistics from advanced RAG system with LazyGraphRAG and Late Chunking*`,
          },
        ] satisfies TextContent[],
      };
    } catch (error) {
      throw new Error(`Failed to get stats: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Memory-Server MCP server running on stdio');
  }
}

// Start the server
const server = new MemoryServerMCP();
server.run().catch((error) => {
  console.error('Failed to start Memory-Server MCP server:', error);
  process.exit(1);
});