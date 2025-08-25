# Search and RAG | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * [Overview](/documentation/overview)
    * [Quickstart](/documentation/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * General

    * [Documents](/documentation/documents)
    * [Conversations](/documentation/conversations)
    * [Collections](/documentation/collections)
    * [Graphs](/documentation/graphs)
    * [Prompts](/documentation/prompts)
    * [Users](/documentation/user-auth)
  * Retrieval

    * [Search and RAG](/documentation/search-and-rag)
    * [Agentic RAG](/documentation/retrieval/agentic-rag)
    * [Hybrid Search](/documentation/hybrid-search)
    * [Advanced RAG](/documentation/advanced-rag)
  * Advanced

    * [Deduplication](/documentation/deduplication)
    * [Contextual Enrichment](/documentation/contextual-enrichment)
  * Other

    * SciPhi Cloud




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Search Modes and Settings](/documentation/search-and-rag#search-modes-and-settings)
  * [AI Powered Search (/retrieval/search)](/documentation/search-and-rag#ai-powered-search-retrievalsearch)
  * [Basic Search Example](/documentation/search-and-rag#basic-search-example)
  * [Hybrid Search Example](/documentation/search-and-rag#hybrid-search-example)
  * [Advanced Filtering](/documentation/search-and-rag#advanced-filtering)
  * [Distance Measures for Vector Search](/documentation/search-and-rag#distance-measures-for-vector-search)
  * [Knowledge Graph Enhanced Retrieval](/documentation/search-and-rag#knowledge-graph-enhanced-retrieval)
  * [Retrieval-Augmented Generation (RAG) (/retrieval/rag)](/documentation/search-and-rag#retrieval-augmented-generation-rag-retrievalrag)
  * [RAG Configuration (rag_generation_config)](/documentation/search-and-rag#rag-configuration-rag_generation_config)
  * [Basic RAG](/documentation/search-and-rag#basic-rag)
  * [RAG with Web Search Integration](/documentation/search-and-rag#rag-with-web-search-integration)
  * [RAG with Hybrid Search](/documentation/search-and-rag#rag-with-hybrid-search)
  * [Streaming RAG](/documentation/search-and-rag#streaming-rag)
  * [Customizing RAG](/documentation/search-and-rag#customizing-rag)
  * [Conclusion](/documentation/search-and-rag#conclusion)



[Retrieval](/documentation/search-and-rag)

# Search and RAG

Copy page

R2R provides powerful search and retrieval capabilities through vector search, full-text search, hybrid search, and Retrieval-Augmented Generation (RAG). The system supports multiple search modes and extensive runtime configuration to help you find and contextualize information effectively.

Refer to the [retrieval API and SDK reference](/api-and-sdks/retrieval/retrieval) for detailed retrieval examples.

## Search Modes and Settings

When using the Search (`/retrieval/search`) or RAG (`/retrieval/rag`) endpoints, you control the retrieval process using `search_mode` and `search_settings`.

  * **`search_mode`** (Optional, defaults to `custom`): Choose between pre-configured modes or full customization.
    * `basic`: Defaults to a simple semantic search configuration. Good for quick setup.
    * `advanced`: Defaults to a hybrid search configuration combining semantic and full-text. Offers broader results.
    * `custom`: Allows full control via the `search_settings` object. If `search_settings` are omitted in `custom` mode, default vector search settings are applied.
  * **`search_settings`** (Optional): A detailed configuration object. If provided alongside `basic` or `advanced` modes, these settings will override the mode’s defaults. Key settings include:
    * `use_semantic_search`: Boolean to enable/disable vector-based semantic search (default: `true` unless overridden).
    * `use_fulltext_search`: Boolean to enable/disable keyword-based full-text search (default: `false` unless using hybrid).
    * `use_hybrid_search`: Boolean to enable hybrid search, combining semantic and full-text (default: `false`). Requires `hybrid_settings`.
    * `filters`: Apply complex filtering rules using MongoDB-like syntax (see “Advanced Filtering” below).
    * `limit`: Integer controlling the maximum number of results to return (default: `10`).
    * `hybrid_settings`: Object to configure weights (`semantic_weight`, `full_text_weight`), limits (`full_text_limit`), and fusion (`rrf_k`) for hybrid search.
    * `chunk_settings`: Object to fine-tune vector index parameters like `index_measure` (distance metric), `probes`, `ef_search`.
    * `search_strategy`: String to enable advanced RAG techniques like `"hyde"` or `"rag_fusion"` (default: `"vanilla"`). See [Advanced RAG](/documentation/advanced-rag).
    * `include_scores`: Boolean to include relevance scores in the results (default: `true`).
    * `include_metadatas`: Boolean to include metadata in the results (default: `true`).



## AI Powered Search (`/retrieval/search`)

R2R offers powerful and highly configurable search capabilities. This endpoint returns raw search results without LLM generation.

### Basic Search Example

This performs a search using default configurations or a specified mode.

###### Python

###### JavaScript

###### Curl
    
    
    1| # Uses default settings (likely semantic search in 'custom' mode)  
    ---|---  
    2| results = client.retrieval.search(  
    3|   query="What is DeepSeek R1?",  
    4| )  
    5|   
    6| # Explicitly using 'basic' mode  
    7| results_basic = client.retrieval.search(  
    8|   query="What is DeepSeek R1?",  
    9|   search_mode="basic",  
    10| )  
  
**Response Structure (`WrappedSearchResponse`):**

The search endpoint returns a `WrappedSearchResponse` containing an `AggregateSearchResult` object with fields like:

  * `results.chunk_search_results`: A list of relevant text `ChunkSearchResult` objects found (containing `id`, `document_id`, `text`, `score`, `metadata`).
  * `results.graph_search_results`: A list of relevant `GraphSearchResult` objects (entities, relationships, communities) if graph search is active and finds results.
  * `results.web_search_results`: A list of `WebSearchResult` objects (if web search was somehow enabled, though typically done via RAG/Agent).


    
    
    1| // Simplified Example Structure  
    ---|---  
    2| {  
    3|   "results": {  
    4|     "chunk_search_results": [  
    5|       {  
    6|         "score": 0.643,  
    7|         "text": "Document Title: DeepSeek_R1.pdf...",  
    8|         "id": "chunk-uuid-...",  
    9|         "document_id": "doc-uuid-...",  
    10|         "metadata": { ... }  
    11|       },  
    12|       // ... more chunks  
    13|     ],  
    14|     "graph_search_results": [  
    15|       // Example: An entity result if graph search ran  
    16|       {  
    17|          "id": "graph-entity-uuid...",  
    18|          "content": { "name": "DeepSeek-R1", "description": "A large language model...", "id": "entity-uuid..." },  
    19|          "result_type": "ENTITY",  
    20|          "score": 0.95,  
    21|          "metadata": { ... }  
    22|       }  
    23|       // ... potentially relationships or communities  
    24|     ],  
    25|     "web_search_results": []  
    26|   }  
    27| }  
  
### Hybrid Search Example

Combine keyword-based (full-text) search with vector search for potentially broader results.

###### Python

###### JavaScript

###### Curl
    
    
    1| hybrid_results = client.retrieval.search(  
    ---|---  
    2|     query="What was Uber's profit in 2020?",  
    3|     search_settings={  
    4|         "use_hybrid_search": True,  
    5|         "hybrid_settings": {  
    6|             "full_text_weight": 1.0,  
    7|             "semantic_weight": 5.0,  
    8|             "full_text_limit": 200, # How many full-text results to initially consider  
    9|             "rrf_k": 50, # Parameter for Reciprocal Rank Fusion  
    10|         },  
    11|         "filters": {"metadata.title": {"$in": ["uber_2021.pdf"]}}, # Filter by metadata field  
    12|         "limit": 10 # Final number of results after fusion/ranking  
    13|     },  
    14| )  
  
### Advanced Filtering

Apply filters to narrow search results based on document properties or metadata. Supported operators include `$eq`, `$neq`, `$gt`, `$gte`, `$lt`, `$lte`, `$like`, `$ilike`, `$in`, `$nin`. You can combine filters using `$and` and `$or`.

###### Python

###### JavaScript
    
    
    1| filtered_results = client.retrieval.search(  
    ---|---  
    2|     query="What are the effects of climate change?",  
    3|     search_settings={  
    4|         "filters": {  
    5|             "$and":[  
    6|                 {"document_type": {"$eq": "pdf"}}, # Assuming 'document_type' is stored  
    7|                 {"metadata.year": {"$gt": 2020}} # Access nested metadata fields  
    8|             ]  
    9|         },  
    10|         "limit": 10  
    11|     }  
    12| )  
  
### Distance Measures for Vector Search

Distance metrics for vector search, which can be configured through the `chunk_settings.index_measure` parameter. Choosing the right distance measure can significantly impact search quality depending on your embeddings and use case:

  * **`cosine_distance`** (Default): Measures the cosine of the angle between vectors, ignoring magnitude. Best for comparing documents regardless of their length.
  * **`l2_distance`** (Euclidean): Measures the straight-line distance between vectors. Useful when both direction and magnitude matter.
  * **`max_inner_product`** : Optimized for finding vectors with similar direction. Good for recommendation systems.
  * **`l1_distance`** (Manhattan): Measures the sum of absolute differences. Less sensitive to outliers than L2.
  * **`hamming_distance`** : Counts the positions at which vectors differ. Best for binary embeddings.
  * **`jaccard_distance`** : Measures dissimilarity between sample sets. Useful for sparse embeddings.



###### Python
    
    
    1| results = client.retrieval.search(  
    ---|---  
    2|   query="What are the key features of quantum computing?",  
    3|   search_settings={  
    4|     "chunk_settings": {  
    5|       "index_measure": "l2_distance"  # Use Euclidean distance instead of default  
    6|     }  
    7|   }  
    8| )  
  
For most text embedding models (e.g., OpenAI’s models), cosine_distance is recommended. For specialized embeddings or specific use cases, experiment with different measures to find the optimal setting for your data.

## Knowledge Graph Enhanced Retrieval

Beyond searching through text chunks, R2R can leverage knowledge graphs to enrich the retrieval process. This offers several benefits:

  * **Contextual Understanding:** Knowledge graphs store information as entities (like people, organizations, concepts) and relationships (like “works for”, “is related to”, “is a type of”). Searching the graph allows R2R to find connections and context that might be missed by purely text-based search.
  * **Relationship-Based Queries:** Answer questions that rely on understanding connections, such as “What projects is Person X involved in?” or “How does Concept A relate to Concept B?”.
  * **Discovering Structure:** Graph search can reveal higher-level structures, such as communities of related entities or key connecting concepts within your data.
  * **Complementary Results:** Graph results (entities, relationships, community summaries) complement text chunks by providing structured information and broader context.



When knowledge graph search is active within R2R, the `AggregateSearchResult` returned by the Search or RAG endpoints may include relevant items in the `graph_search_results` list, enhancing the context available for understanding or generation.

## Retrieval-Augmented Generation (RAG) (`/retrieval/rag`)

R2R’s RAG engine combines the search capabilities above (including text, vector, hybrid, and potentially graph results) with Large Language Models (LLMs) to generate contextually relevant responses grounded in your ingested documents and optional web search results.

### RAG Configuration (`rag_generation_config`)

Control the LLM’s generation process:

  * `model`: Specify the LLM to use (e.g., `"openai/gpt-4o-mini"`, `"anthropic/claude-3-haiku-20240307"`). Defaults are set in R2R config.
  * `stream`: Boolean (default `false`). Set to `true` for streaming responses.
  * `temperature`, `max_tokens`, `top_p`, etc.: Standard LLM generation parameters.



### Basic RAG

Generate a response using retrieved context. Uses the same `search_mode` and `search_settings` as the search endpoint to find relevant information.

###### Python

###### JavaScript

###### Curl
    
    
    1| # Basic RAG call using default search and generation settings  
    ---|---  
    2| rag_response = client.retrieval.rag(query="What is DeepSeek R1?")  
  
**Response Structure (`WrappedRAGResponse`):**

The non-streaming RAG endpoint returns a `WrappedRAGResponse` containing an `RAGResponse` object with fields like:

  * `results.generated_answer`: The final synthesized answer from the LLM.
  * `results.search_results`: The `AggregateSearchResult` used to generate the answer (containing chunks, possibly graph results, and web results).
  * `results.citations`: A list of `Citation` objects linking parts of the answer to specific sources (`ChunkSearchResult`, `GraphSearchResult`, `WebSearchResult`, etc.) found in `search_results`. Each citation includes an `id` (short identifier used in the text like `[1]`) and a `payload` containing the source object.
  * `results.metadata`: LLM provider metadata about the generation call.


    
    
    1| // Simplified Example Structure  
    ---|---  
    2| {  
    3|   "results": {  
    4|     "generated_answer": "DeepSeek-R1 is a model that... [1]. It excels in tasks... [2].",  
    5|     "search_results": {  
    6|       "chunk_search_results": [ { "id": "chunk-abc...", "text": "...", "score": 0.8 }, /* ... */ ],  
    7|       "graph_search_results": [ { /* Graph Entity/Relationship */ } ],  
    8|       "web_search_results": [ { "url": "...", "title": "...", "snippet": "..." }, /* ... */ ]  
    9|     },  
    10|     "citations": [  
    11|       {  
    12|         "id": "cit.1", // Corresponds to [1] in text  
    13|         "object": "citation",  
    14|         "payload": { /* ChunkSearchResult for chunk-abc... */ }  
    15|       },  
    16|       {  
    17|         "id": "cit.2", // Corresponds to [2] in text  
    18|         "object": "citation",  
    19|         "payload": { /* WebSearchResult for relevant web page */ }  
    20|       }  
    21|       // ... more citations potentially linking to graph results too  
    22|     ],  
    23|     "metadata": { "model": "openai/gpt-4o-mini", ... }  
    24|   }  
    25| }  
  
### RAG with Web Search Integration

Enhance RAG responses with up-to-date information from the web by setting `include_web_search=True`.

###### Python

###### JavaScript

###### Curl
    
    
    1| web_rag_response = client.retrieval.rag(  
    ---|---  
    2|     query="What are the latest developments with DeepSeek R1?",  
    3|     include_web_search=True  
    4| )  
  
When enabled, R2R performs a web search using the query, and the results are added to the context provided to the LLM alongside results from your documents or knowledge graph.

### RAG with Hybrid Search

Combine hybrid search with RAG by configuring `search_settings`.

###### Python

###### JavaScript

###### Curl
    
    
    1| hybrid_rag_response = client.retrieval.rag(  
    ---|---  
    2|     query="Who is Jon Snow?",  
    3|     search_settings={"use_hybrid_search": True}  
    4| )  
  
### Streaming RAG

Receive RAG responses as a stream of Server-Sent Events (SSE) by setting `stream: True` in `rag_generation_config`. This is ideal for real-time applications.

**Event Types:**

  1. `search_results`: Contains the initial `AggregateSearchResult` (sent once at the beginning).
     * `data`: The full `AggregateSearchResult` object (chunks, potentially graph results, web results).
  2. `message`: Streams partial tokens of the response as they are generated.
     * `data.delta.content`: The text chunk being streamed.
  3. `citation`: Indicates when a citation source is identified. Sent _once_ per unique source when it’s first referenced.
     * `data.id`: The short citation ID (e.g., `"cit.1"`).
     * `data.payload`: The full source object (`ChunkSearchResult`, `GraphSearchResult`, `WebSearchResult`, etc.).
     * `data.is_new`: True if this is the first time this citation ID is sent.
     * `data.span`: The start/end character indices in the _current_ accumulated text where the citation marker (e.g., `[1]`) appears.
  4. `final_answer`: Sent once at the end, containing the complete generated answer and structured citations.
     * `data.generated_answer`: The full final text.
     * `data.citations`: List of all citations, including their `id`, `payload`, and all `spans` where they appeared in the final text.



###### Python

###### JavaScript
    
    
    1| from r2r import (  
    ---|---  
    2|     CitationEvent,  
    3|     FinalAnswerEvent,  
    4|     MessageEvent,  
    5|     SearchResultsEvent,  
    6|     R2RClient,  
    7|     # Assuming ThinkingEvent is imported if needed, though not standard in basic RAG  
    8| )  
    9|   
    10| # Set stream=True in rag_generation_config  
    11| result_stream = client.retrieval.rag(  
    12|     query="What is DeepSeek R1?",  
    13|     search_settings={"limit": 25},  
    14|     rag_generation_config={"stream": True, "model": "openai/gpt-4o-mini"},  
    15|     include_web_search=True,  
    16| )  
    17|   
    18| for event in result_stream:  
    19|     if isinstance(event, SearchResultsEvent):  
    20|         print(f"Search results received (Chunks: {len(event.data.data.chunk_search_results)}, Graph: {len(event.data.data.graph_search_results)}, Web: {len(event.data.data.web_search_results)})")  
    21|     elif isinstance(event, MessageEvent):  
    22|         # Access the actual text delta  
    23|         if event.data.delta and event.data.delta.content and event.data.delta.content[0].type == 'text' and event.data.delta.content[0].payload.value:  
    24|              print(event.data.delta.content[0].payload.value, end="", flush=True)  
    25|     elif isinstance(event, CitationEvent):  
    26|         # Payload is only sent when is_new is True  
    27|         if event.data.is_new:  
    28|             print(f"\n<<< New Citation Source Detected: ID={event.data.id} >>>")  
    29|   
    30|     elif isinstance(event, FinalAnswerEvent):  
    31|         print("\n\n--- Final Answer ---")  
    32|         print(event.data.generated_answer)  
    33|         print("\n--- Citations Summary ---")  
    34|         for cit in event.data.citations:  
    35|              print(f"  ID: {cit.id}, Spans: {cit.span}")  
  
### Customizing RAG

Besides `search_settings`, you can customize RAG generation using `rag_generation_config`.

Example of customizing the model with web search:

###### Python

###### JavaScript

###### Curl
    
    
    1| # Requires ANTHROPIC_API_KEY env var if using Anthropic models  
    ---|---  
    2| response = client.retrieval.rag(  
    3|   query="Who was Aristotle and what are his recent influences?",  
    4|   rag_generation_config={  
    5|       "model":"anthropic/claude-3-haiku-20240307",  
    6|       "stream": False, # Get a single response object  
    7|       "temperature": 0.5  
    8|   },  
    9|   include_web_search=True  
    10| )  
    11| print(response.results.generated_answer)  
  
## Conclusion

R2R’s search and RAG capabilities provide flexible tools for finding and contextualizing information. Whether you need simple semantic search, advanced hybrid retrieval with filtering, or customizable RAG generation incorporating document chunks, knowledge graph insights, and web results via streaming or single responses, the system can be configured to meet your specific needs.

For more advanced use cases:

  * Explore advanced RAG strategies like HyDE and RAG-Fusion in [Advanced RAG](/documentation/advanced-rag).
  * Learn about the conversational [Agentic RAG](/documentation/retrieval/agentic-rag) system for multi-turn interactions.
  * Dive deeper into specific configuration options in the [API & SDK Reference](/api-and-sdks/retrieval/retrieval).



Was this page helpful?

YesNo

[Previous](/documentation/user-auth)#### [Agentic RAGNext](/documentation/retrieval/agentic-rag)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Introduction | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  *     * [Introduction](/introduction)
    * [System](/introduction/system)
    * [What's New](/introduction/whats-new)
  * Guides

    * [What is R2R?](/introduction/what-is-r2r)
    * [More about RAG](/introduction/rag)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Cloud Documentation](/introduction#cloud-documentation)
  * [Getting Started](/introduction#getting-started)
  * [Key Features](/introduction#key-features)
  * [Ingestion & Retrieval](/introduction#ingestion--retrieval)
  * [Application Layer](/introduction#application-layer)
  * [Self-Hosting](/introduction#self-hosting)
  * [Community](/introduction#community)
  * [About](/introduction#about)



# Introduction

Copy page

The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

![r2r](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/r2r.png)

R2R is an all-in-one solution for AI Retrieval-Augmented Generation (RAG) with production-ready features, including multimodal content ingestion, hybrid search functionality, configurable GraphRAG, and user/document management.

R2R also includes a **Deep Research API** , a multi-step reasoning system that fetches relevant data from your knowledgebase and/or the internet to deliver richer, context-aware answers for complex queries.

* * *

# Cloud Documentation

## Getting Started

  * 🚀 **[Quickstart](/documentation/quickstart)** A quick introduction to R2R’s core features.
  * ❇️ **[API& SDKs](/api-and-sdks/introduction)** API reference and Python/JS SDKs for interacting with R2R.



## Key Features

### Ingestion & Retrieval

  * **📁[Multimodal Ingestion](/self-hosting/configuration/ingestion)** Parse `.txt`, `.pdf`, `.json`, `.png`, `.mp3`, and more.
  * **🔍[Hybrid Search](/documentation/search-and-rag)** Combine semantic and keyword search with reciprocal rank fusion for enhanced relevancy.
  * **🔗[Knowledge Graphs](/cookbooks/graphs)** Automatically extract entities and relationships to build knowledge graphs.
  * **🤖[Agentic RAG](/documentation/retrieval/agentic-rag)** R2R’s powerful Deep Research agent integrated with RAG over your knowledgebase.



### Application Layer

  * 💻 **[Web Development](/cookbooks/web-dev)** Building web apps using R2R.
  * 🔐 **[User Auth](/documentation/user-auth)** Authenticating users.
  * 📂 **[Collections](/self-hosting/collections)** Document collections management.
  * 🌐 **[Web Application](/cookbooks/web-dev)** Connecting with the R2R Application.



### Self-Hosting

  * 🐋 **[Docker](/self-hosting/installation/full)** Use Docker to easily deploy the full R2R system into your local environment
  * 🧩 **[Configuration](/self-hosting/configuration/overview)** Set up your application using intuitive configuration files.



* * *

# Community

[Join our Discord server](https://discord.gg/p6KqD2kjtB) to get support and connect with both the R2R team and other developers. Whether you’re encountering issues, seeking best practices, or sharing your experiences, we’re here to help.

* * *

# About

  * **🌐[SciPhi Website](https://sciphi.ai/)** Explore a managed AI solution powered by R2R.
  * **✉️[Contact Us](mailto:///founders@sciphi.ai)** Get in touch with our team to discuss your specific needs.



Was this page helpful?

YesNo

#### [SystemLearn about the R2R system architectureNext](/introduction/system)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# R2R API & SDKs | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * API Documentation

    * [R2R API & SDKs](/api-and-sdks/introduction)
  * API & SDKs

    * Retrieval

    * Documents

    * Graphs

    * Indices

    * Users

    * Collections

    * Conversations

    * Prompts

    * Chunks

    * System




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Welcome to the R2R API & SDK Reference](/api-and-sdks/introduction#welcome-to-the-r2r-api--sdk-reference)
  * [Key Features](/api-and-sdks/introduction#key-features)
  * [Getting Started](/api-and-sdks/introduction#getting-started)



[API Documentation](/api-and-sdks/introduction)

# 

R2R API & SDKs

Copy page

Powerful document ingestion, search, and RAG capabilities at your fingertips

## Welcome to the R2R API & SDK Reference

R2R is a powerful library that offers both methods and a REST API for document ingestion, Retrieval-Augmented Generation (RAG), evaluation, and additional features like observability, analytics, and document management. This API documentation will guide you through the various endpoints and functionalities R2R provides.

##### 

This API documentation is designed to help developers integrate R2R’s capabilities into their applications efficiently. Whether you’re building a search engine, a question-answering system, or a document management solution, the R2R API has you covered.

## Key Features

R2R API offers a wide range of features, including:

  * Document Ingestion and Management
  * AI-Powered Search (Vector, Hybrid, and Knowledge Graph)
  * Retrieval-Augmented Generation (RAG)
  * User Auth & Management
  * Observability and Analytics



[R2R GitHub RepositoryView the R2R source code and contribute](https://github.com/SciPhi-AI/R2R)

## Getting Started

To get started with the R2R API, you’ll need to:

  1. Install R2R in your environment
  2. Run the server with `python -m r2r.serve`, or customize your FastAPI for production settings.



For detailed installation and setup instructions, please refer to our [Installation Guide](/self-hosting/installation/overview).

Was this page helpful?

YesNo

#### [RetrievalNext](/api-and-sdks/retrieval/retrieval)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Overview | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * [Overview](/documentation/overview)
    * [Quickstart](/documentation/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * General

    * [Documents](/documentation/documents)
    * [Conversations](/documentation/conversations)
    * [Collections](/documentation/collections)
    * [Graphs](/documentation/graphs)
    * [Prompts](/documentation/prompts)
    * [Users](/documentation/user-auth)
  * Retrieval

    * [Search and RAG](/documentation/search-and-rag)
    * [Agentic RAG](/documentation/retrieval/agentic-rag)
    * [Hybrid Search](/documentation/hybrid-search)
    * [Advanced RAG](/documentation/advanced-rag)
  * Advanced

    * [Deduplication](/documentation/deduplication)
    * [Contextual Enrichment](/documentation/contextual-enrichment)
  * Other

    * SciPhi Cloud




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

[Getting Started](/documentation/overview)

# Overview

Copy page

R2R is the most advanced AI retrieval system. And with R2R, getting your AI application started is simple.

R2R offers powerful features for your applications, including:

  * **Cutting Edge Search** : Advanced RAG techniques like [hybrid search](/documentation/hybrid-search), [knowledge graphs](/documentation/graphs), [advanced RAG](/documentation/advanced-rag), and [agentic retrieval](/documentation/retrieval/agentic-rag).
  * **Flexibility** : Runtime configuration makes it easy to adjust and tune R2R to fit your needs.
  * **Scale** : Handle increasing workloads and large datasets, designed specifically for performance.
  * **Auth & Collection**: Production must-haves like user [auth](/documentation/user-auth) and [document collections](/documentation/collections).



[CloudGet started using R2R through SciPhi Cloud, free of charge. **Perfect for fast serverless deployment**.](/documentation/quickstart)[Self HostedHost your own full-featured R2R system. Ideal **for on premise use cases**.](/self-hosting/installation/overview)

Choose the system that best aligns with your requirements and proceed with the documentation.

Was this page helpful?

YesNo

#### [QuickstartNext](/documentation/quickstart)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Ingestion | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Data Processing and Retrieval

    * [Ingestion](/cookbooks/ingestion)
    * [Knowledge Graphs](/cookbooks/graphs)
    * [User-Defined Agent Tools](/cookbooks/custom-tools)
  * System Operations

    * [Email Verification](/cookbooks/email)
    * [Maintenance & Scaling](/cookbooks/maintenance)
    * [Orchestration](/cookbooks/orchestration)
  * Other

    * [Local LLMs](/cookbooks/local-llms)
    * [Structured Output](/cookbooks/structured-output)
    * [MCP](/cookbooks/other/mcp)
    * [Web Development](/cookbooks/web-dev)
    * [Evals](/cookbooks/other/evals)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Introduction](/cookbooks/ingestion#introduction)
  * [Supported File Types](/cookbooks/ingestion#supported-file-types)
  * [Ingestion Modes](/cookbooks/ingestion#ingestion-modes)
  * [Ingesting Documents](/cookbooks/ingestion#ingesting-documents)
  * [Ingesting Pre-Processed Chunks](/cookbooks/ingestion#ingesting-pre-processed-chunks)
  * [Deleting Documents and Chunks](/cookbooks/ingestion#deleting-documents-and-chunks)
  * [Additional Configuration & Concepts](/cookbooks/ingestion#additional-configuration--concepts)
  * [Conclusion](/cookbooks/ingestion#conclusion)



[Data Processing and Retrieval](/cookbooks/ingestion)

# Ingestion

Copy page

Learn how to ingest, update, and delete documents with R2R

## Introduction

R2R provides a powerful and flexible ingestion to process and manage various types of documents. It supports a wide range of file formats—text, documents, PDFs, images, audio, and even video—and transforms them into searchable, analyzable content. The ingestion process includes parsing, chunking, embedding, and optionally extracting entities and relationships for knowledge graph construction.

This cookbook will guide you through:

  * Ingesting files, raw text, or pre-processed chunks
  * Choosing an ingestion mode (`fast`, `hi-res`, `ocr`, or `custom`)
  * Updating and deleting documents and chunks



For more on configuring ingestion, see the [Ingestion Configuration Overview](/self-hosting/configuration/ingestion).

### Supported File Types

R2R supports ingestion of the following document types:

Category| File types  
---|---  
Image| `.bmp`, `.heic`, `.jpeg`, `.png`, `.tiff`  
MP3| `.mp3`  
PDF| `.pdf`  
CSV| `.csv`  
E-mail| `.eml`, `.msg`, `.p7s`  
EPUB| `.epub`  
Excel| `.xls`, `.xlsx`  
HTML| `.html`  
Markdown| `.md`  
Org Mode| `.org`  
Open Office| `.odt`  
Plain text| `.txt`  
PowerPoint| `.ppt`, `.pptx`  
reStructured Text| `.rst`  
Rich Text| `.rtf`  
TSV| `.tsv`  
Word| `.doc`, `.docx`  
Code| `.py`, `.js`, `.ts`, `.css`  
  
## Ingestion Modes

R2R offers four primary ingestion modes to tailor the process to your requirements:

  * **`fast`** :  
A speed-oriented ingestion mode that prioritizes rapid processing with minimal enrichment. Summaries and some advanced parsing are skipped, making this ideal for quickly processing large volumes of documents.

  * **`hi-res`** :  
A comprehensive, high-quality ingestion mode that may leverage multimodal foundation models (visual language models) for parsing complex documents and PDFs, even integrating image-based content.

    * On a **lite** deployment, R2R uses its built-in (`r2r`) parser.
    * On a **full** deployment, it can use `unstructured_local` or `unstructured_api` for more robust parsing and advanced features.  
Choose `hi-res` mode if you need the highest quality extraction, including image-to-text analysis and richer semantic segmentation.
  * **`ocr`** : OCR mode utilizes optical character recognition models to convert PDFs to markdown. Currently, this mode requires use of Mistral OCR.

  * **`custom`** :  
For advanced users who require fine-grained control. In `custom` mode, you provide a full `ingestion_config` dict or object to specify every detail: parser options, chunking strategy, character limits, and more.




**Example Usage:**
    
    
    1| file_path = 'path/to/file.txt'  
    ---|---  
    2| metadata = {'key1': 'value1'}  
    3|   
    4| # hi-res mode for thorough extraction  
    5| client.documents.create(  
    6|     file_path=file_path,  
    7|     metadata=metadata,  
    8|     ingestion_mode="hi-res"  
    9| )  
    10|   
    11| # fast mode for quick processing  
    12| client.documents.create(  
    13|     file_path=file_path,  
    14|     ingestion_mode="fast"  
    15| )  
    16|   
    17| # custom mode for full control  
    18| client.documents.create(  
    19|     file_path=file_path,  
    20|     ingestion_mode="custom",  
    21|     ingestion_config={  
    22|         "provider": "unstructured_local",  
    23|         "strategy": "auto",  
    24|         "chunking_strategy": "by_title",  
    25|         "new_after_n_chars": 256,  
    26|         "max_characters": 512,  
    27|         "combine_under_n_chars": 64,  
    28|         "overlap": 100,  
    29|     }  
    30| )  
  
## Ingesting Documents

A `Document` represents ingested content in R2R. When you ingest a file, text, or chunks:

  1. The file (or text) is parsed into text.
  2. Text is chunked into manageable units.
  3. Embeddings are generated for semantic search.
  4. Content is stored for retrieval and optionally linked to the knowledge graph.



In a **full** R2R installation, ingestion is asynchronous. You can monitor ingestion status and confirm when documents are ready:
    
    
    1| client.documents.list()  
    ---|---  
    2|   
    3| # [  
    4| #  DocumentResponse(  
    5| #    id=UUID('e43864f5-a36f-548e-aacd-6f8d48b30c7f'),   
    6| #    collection_ids=[UUID('122fdf6a-e116-546b-a8f6-e4cb2e2c0a09')],   
    7| #    owner_id=UUID('2acb499e-8428-543b-bd85-0d9098718220'),   
    8| #    document_type=<DocumentType.PDF: 'pdf'>,   
    9| #    metadata={'title': 'DeepSeek_R1.pdf', 'version': 'v0'},   
    10| #    version='v0',   
    11| #    size_in_bytes=1768572,   
    12| #    ingestion_status=<IngestionStatus.SUCCESS: 'success'>,   
    13| #    extraction_status=<GraphExtractionStatus.PENDING: 'pending'>,   
    14| #    created_at=datetime.datetime(2025, 2, 8, 3, 31, 39, 126759, tzinfo=TzInfo(UTC)),   
    15| #    updated_at=datetime.datetime(2025, 2, 8, 3, 31, 39, 160114, tzinfo=TzInfo(UTC)),   
    16| #    ingestion_attempt_number=None,   
    17| #    summary="The document contains a comprehensive overview of DeepSeek-R1, a series of reasoning models developed by DeepSeek-AI, which includes DeepSeek-R1-Zero and DeepSeek-R1. DeepSeek-R1-Zero utilizes large-scale reinforcement learning (RL) without supervised fine-tuning, showcasing impressive reasoning capabilities but facing challenges like readability and language mixing. To enhance performance, DeepSeek-R1 incorporates multi-stage training and cold-start data, achieving results comparable to OpenAI's models on various reasoning tasks. The document details the models' training processes, evaluation results across multiple benchmarks, and the introduction of distilled models that maintain reasoning capabilities while being smaller and more efficient. It also discusses the limitations of current models, such as language mixing and sensitivity to prompts, and outlines future research directions to improve general capabilities and efficiency in software engineering tasks. The findings emphasize the potential of RL in developing reasoning abilities in large language models and the effectiveness of distillation techniques for smaller models.", summary_embedding=None, total_tokens=29673)] total_entries=1  
    18| #   ), ...  
    19| # ]  
  
An `ingestion_status` of `"success"` confirms the document is fully ingested. You can also check the R2R dashboard at [http://localhost:7273](http://localhost:7273/) for ingestion progress and status.

For more details on creating documents, [refer to the Create Document API](/api-and-sdks/documents/create-document).

## Ingesting Pre-Processed Chunks

If you have pre-processed chunks from your own pipeline, you can directly ingest them. This is especially useful if you’ve already divided content into logical segments.
    
    
    1| chunks = ["This is my first parsed chunk", "This is my second parsed chunk"]  
    ---|---  
    2| client.documents.create(  
    3|     chunks=chunks,  
    4|     ingestion_mode="fast"  # use fast for a quick chunk ingestion  
    5| )  
  
## Deleting Documents and Chunks

To remove documents or chunks, call their respective `delete` methods:
    
    
    1| # Delete a document  
    ---|---  
    2| delete_response = client.documents.delete(document_id)  
    3|   
    4| # Delete a chunk  
    5| delete_response = client.chunks.delete(chunk_id)  
  
You can also delete documents by specifying filters using the [`by-filter`](/api-and-sdks/documents/delete-document-by-filter) route.

## Additional Configuration & Concepts

  * **Light vs. Full Deployments:**

    * Light (default) uses R2R’s built-in parser and supports synchronous ingestion.
    * Full deployments orchestrate ingestion tasks asynchronously and integrate with more complex providers like `unstructured_local`.
  * **Provider Configuration:**  
Settings in `r2r.toml` or at runtime (`ingestion_config`) can adjust parsing and chunking strategies:

    * `fast` and `hi-res` modes are influenced by strategies like `"auto"` or `"hi_res"` in the unstructured provider.
    * `custom` mode allows you to override chunk size, overlap, excluded parsers, and more at runtime.



For detailed configuration options, see:

  * [Data Ingestion Configuration](/self-hosting/configuration/ingestion)



## Conclusion

R2R’s ingestion is flexible and efficient, allowing you to tailor ingestion to your needs:

  * Use `fast` for quick processing.
  * Use `hi-res` for high-quality, multimodal analysis.
  * Use `custom` for advanced, granular control.



You can easily ingest documents or pre-processed chunks, update their content, and delete them when no longer needed. Combined with powerful retrieval and knowledge graph capabilities, R2R enables seamless integration of advanced document management into your applications.

Was this page helpful?

YesNo

#### [Knowledge GraphsBuilding and managing graphs through collectionsNext](/cookbooks/graphs)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# System | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  *     * [Introduction](/introduction)
    * [System](/introduction/system)
    * [What's New](/introduction/whats-new)
  * Guides

    * [What is R2R?](/introduction/what-is-r2r)
    * [More about RAG](/introduction/rag)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [System Diagram](/introduction/system#system-diagram)
  * [System Overview](/introduction/system#system-overview)



# System

Copy page

Learn about the R2R system architecture

## System Diagram

## System Overview

R2R is built on a modular, service-oriented architecture designed for scalability and flexibility:

  1. **API Layer** : A RESTful API cluster handles incoming requests, routing them to appropriate services.

  2. **Core Services** : Specialized services for authentication, retrieval, ingestion, graph building, and app management.

  3. **Orchestration** : Manages complex workflows and long-running tasks using a message queue system.

  4. **Storage** : Utilizes Postgres with `pgvector` and full-text search for vector storage and search, and graph search.

  5. **Providers** : Pluggable components for parsing, embedding, authenticating, and retrieval-augmented generation.

  6. **R2R Application** : A React+Next.js app providing a user interface for interacting with the R2R system.




This architecture enables R2R to handle everything from simple RAG applications to complex, production-grade systems with advanced features like hybrid search and GraphRAG.

Ready to get started? Check out our [Docker installation guide](/self-hosting/installation/full) and [Quickstart tutorial](/documentation/quickstart) to begin your R2R journey.

Was this page helpful?

YesNo

[Previous](/introduction)#### [What's NewChangelogNext](/introduction/whats-new)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# What's New | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  *     * [Introduction](/introduction)
    * [System](/introduction/system)
    * [What's New](/introduction/whats-new)
  * Guides

    * [What is R2R?](/introduction/what-is-r2r)
    * [More about RAG](/introduction/rag)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Version 0.3.5 — March. 2025](/introduction/whats-new#version-035--march-2025)
  * [New Features](/introduction/whats-new#new-features)
  * [Bug Fixes](/introduction/whats-new#bug-fixes)



# What's New

Copy page

Changelog

## Version 0.3.5 — March. 2025

### New Features

  * Improved API released for Agentic RAG [(agentic-rag)](/documentation/retrieval/agentic-rag)
  * SSE streaming output for RAG
  * Improved citations for robust provenance



### Bug Fixes

  * Minor bug fixes around local LLM setup / operation



Was this page helpful?

YesNo

[Previous](/introduction/system)#### [What is R2R?Next](/introduction/what-is-r2r)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Collections | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * Installation

    * [Quickstart](/self-hosting/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * Configuration Files

    * [Overview](/self-hosting/configuration/overview)
    * [Database](/self-hosting/configuration/database)
    * [File Storage](/self-hosting/configuration/file-storage)
    * [Embedding](/self-hosting/configuration/embedding)
    * [LLMs](/self-hosting/configuration/llm)
    * [Email](/self-hosting/configuration/email)
    * [Crypto](/self-hosting/configuration/crypto)
    * [Auth](/self-hosting/configuration/auth)
    * [Scheduler](/self-hosting/configuration/scheduler)
    * [Orchestration](/self-hosting/configuration/orchestration)
    * [Agent](/self-hosting/configuration/agent)
    * [Ingestion](/self-hosting/configuration/ingestion)
  * Retrieval and generation

    * [Overview](/self-hosting/configuration/retrieval/overview)
    * [RAG](/self-hosting/configuration/retrieval/rag)
    * [Graphs](/self-hosting/configuration/knowledge-graph/overview)
    * [Prompts](/self-hosting/configuration/retrieval/prompts)
  * System

    * [Local LLMs](/self-hosting/local-rag)
  * Deployment

    * [Introduction](/self-hosting/deployment/introduction)
    * Cloud Providers

  * Users

    * [User Auth](/self-hosting/user-auth)
    * [Collections](/self-hosting/collections)
    * [Application](/self-hosting/application)
  * Other

    * Telemetry




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Introduction](/self-hosting/collections#introduction)
  * [Basic Usage](/self-hosting/collections#basic-usage)
  * [Collection CRUD operations](/self-hosting/collections#collection-crud-operations)
  * [Listing Collections](/self-hosting/collections#listing-collections)
  * [User Management in Collections](/self-hosting/collections#user-management-in-collections)
  * [Adding a User to a Collection](/self-hosting/collections#adding-a-user-to-a-collection)
  * [Removing a User from a Collections](/self-hosting/collections#removing-a-user-from-a-collections)
  * [Listing Users in a Collection](/self-hosting/collections#listing-users-in-a-collection)
  * [Getting Collections for a User](/self-hosting/collections#getting-collections-for-a-user)
  * [Document Management in Collections](/self-hosting/collections#document-management-in-collections)
  * [Assigning a Document to a Collection](/self-hosting/collections#assigning-a-document-to-a-collection)
  * [Removing a Document from a Collection](/self-hosting/collections#removing-a-document-from-a-collection)
  * [Listing Documents in a Collection](/self-hosting/collections#listing-documents-in-a-collection)
  * [Getting Collections for a Document](/self-hosting/collections#getting-collections-for-a-document)
  * [Advanced Collection Management](/self-hosting/collections#advanced-collection-management)
  * [Generating Synthetic Descriptions](/self-hosting/collections#generating-synthetic-descriptions)
  * [Collection Overview](/self-hosting/collections#collection-overview)
  * [Deleting a Collection](/self-hosting/collections#deleting-a-collection)
  * [Pagination and Filtering](/self-hosting/collections#pagination-and-filtering)
  * [Security Considerations](/self-hosting/collections#security-considerations)
  * [Customizing Collection Permissions](/self-hosting/collections#customizing-collection-permissions)
  * [Troubleshooting](/self-hosting/collections#troubleshooting)
  * [Conclusion](/self-hosting/collections#conclusion)



[Users](/self-hosting/user-auth)

# Collections

Copy page

A comprehensive guide to creating collections in R2R

## Introduction

A collection in R2R is a logical grouping of users and documents that allows for efficient access control and organization. Collections enable you to manage permissions and access to documents at a group level, rather than individually.

R2R provides robust document collection management, allowing developers to implement efficient access control and organization of users and documents. This cookbook will guide you through the collection capabilities in R2R.

For user authentication, please refer to the [User Auth Cookbook](/documentation/user-auth).

##### 

Collection permissioning in R2R is still under development and as a result the is likely to API continue evolving in future releases.

_A diagram showing user and collection management across r2r_

## Basic Usage

##### 

Collections currently follow a flat hierarchy wherein superusers are responsible for management operations. This functionality will expand as development on R2R continues.

### Collection CRUD operations

Let’s start by creating a new collection:
    
    
    1| from r2r import R2RClient  
    ---|---  
    2|   
    3| client = R2RClient("http://localhost:7272")  # Replace with your R2R deployment URL  
    4|   
    5| # Assuming you're logged in as an admin or a user with appropriate permissions  
    6| # For testing, the default R2R implementation will grant superuser privileges to anon api calls  
    7| collection_result = client.collections.create("Marketing Team", "Collection for marketing department")  
    8|   
    9| print(f"Collection creation result: {collection_result}")  
    10| # {'results': {'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Marketing Team', 'description': 'Collection for marketing department', 'created_at': '2024-07-16T22:53:47.524794Z', 'updated_at': '2024-07-16T22:53:47.524794Z'}}  
  
To retrieve details about a specific collection:
    
    
    1| collection_id = '123e4567-e89b-12d3-a456-426614174000'  # Use the collection_id from the creation result  
    ---|---  
    2| collection_details = client.collections.retrieve(collection_id)  
    3|   
    4| print(f"Collection details: {collection_details}")  
    5| # {'results': {'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Marketing Team', 'description': 'Collection for marketing department', 'created_at': '2024-07-16T22:53:47.524794Z', 'updated_at': '2024-07-16T22:53:47.524794Z'}}  
  
You can update a collection’s name or description:
    
    
    1| update_result = client.collections.update(  
    ---|---  
    2|     collection_id,  
    3|     name="Updated Marketing Team",  
    4|     description="New description for marketing team"  
    5| )  
    6|   
    7| print(f"Collection update result: {update_result}")  
    8| # {'results': {'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Updated Marketing Team', 'description': 'New description for marketing team', 'created_at': '2024-07-16T22:53:47.524794Z', 'updated_at': '2024-07-16T23:15:30.123456Z'}}  
  
Lastly, you can delete a collection

### Listing Collections
    
    
    1| client.collections.delete(collection_id)  
    ---|---  
  
To get a list of all collections:
    
    
    1| collections_list = client.collections.list()  
    ---|---  
    2|   
    3| print(f"Collections list: {collections_list}")  
    4| # {'results': [{'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Updated Marketing Team', 'description': 'New description for marketing team', 'created_at': '2024-07-16T22:53:47.524794Z', 'updated_at': '2024-07-16T23:15:30.123456Z'}, ...]}  
  
## User Management in Collections

### Adding a User to a Collection

To add a user to a collection, you need both the user’s ID and the collections’s ID:
    
    
    1| user_id = '456e789f-g01h-34i5-j678-901234567890'  # This should be a valid user ID  
    ---|---  
    2| collection_id = '123e4567-e89b-12d3-a456-426614174000' # this should be a collection I own  
    3| add_user_result = client.collections.add_user(user_id, collection_id)  
    4|   
    5| print(f"Add user to collection result: {add_user_result}")  
    6| # {'results': {'message': 'User successfully added to the collection'}}  
  
### Removing a User from a Collections

Similarly, to remove a user from a collection:
    
    
    1| remove_user_result = client.collections.remove_user(user_id, collection_id)  
    ---|---  
    2|   
    3| print(f"Remove user from collection result: {remove_user_result}")  
    4| # {'results': None}  
  
### Listing Users in a Collection

To get a list of all users in a specific collection:
    
    
    1| users_in_collection = client.collections.list_users(collection_id)  
    ---|---  
    2|   
    3| print(f"Users in collection: {users_in_collection}")  
    4| # {'results': [{'user_id': '456e789f-g01h-34i5-j678-901234567890', 'email': 'user@example.com', 'name': 'John Doe', ...}, ...]}  
  
### Getting Collections for a User

To get all collections that a user is a member of:
    
    
    1| user.list_collections = client.user.list_collections(user_id)  
    ---|---  
    2|   
    3| print(f"User's collections: {user.list_collections}")  
    4| # {'results': [{'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Updated Marketing Team', ...}, ...]}  
  
## Document Management in Collections

### Assigning a Document to a Collection

To assign a document to a collection:
    
    
    1| document_id = '789g012j-k34l-56m7-n890-123456789012'  # This should be a valid document ID  
    ---|---  
    2| assign_doc_result = client.collections.add_document(collection_id, document_id)  
    3|   
    4| print(f"Assign document to collection result: {assign_doc_result}")  
    5| # {'results': {'message': 'Document successfully assigned to the collection'}}  
  
### Removing a Document from a Collection

To remove a document from a collection:
    
    
    1| remove_doc_result = client.collections.remove_document(collection_id, document_id)  
    ---|---  
    2|   
    3| print(f"Remove document from collection result: {remove_doc_result}")  
    4| # {'results': {'message': 'Document successfully removed from the collection'}}  
  
### Listing Documents in a Collection

To get a list of all documents in a specific collection:
    
    
    1| docs_in_collection = client.collections.list_documents(collection_id)  
    ---|---  
    2|   
    3| print(f"Documents in collection: {docs_in_collection}")  
    4| # {'results': [{'document_id': '789g012j-k34l-56m7-n890-123456789012', 'title': 'Marketing Strategy 2024', ...}, ...]}  
  
### Getting Collections for a Document

To get all collections that a document is assigned to:
    
    
    1| documents.list_collections = client.documents.list_collections(document_id)  
    ---|---  
    2|   
    3| print(f"Document's collections: {documents.list_collections}")  
    4| # {'results': [{'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Updated Marketing Team', ...}, ...]}  
  
## Advanced Collection Management

### Generating Synthetic Descriptions

To have an LLM generate a description for a collection, you can run:
    
    
    1| update_result = client.collections.update(  
    ---|---  
    2|     collection_id,  
    3|     generate_description=True  
    4| )  
    5|   
    6| print(f"Collection update result: {update_result}")  
    7| # {'results': {'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Updated Marketing Team', 'description': 'A rich description generated over the summaries of the documents in the collection', 'created_at': '2024-07-16T22:53:47.524794Z', 'updated_at': '2024-07-16T23:15:30.123456Z'}}  
  
This is particularly helpful when building graphs as the summary provides high-quality context in the prompt, resulting in better descriptions.

### Collection Overview

To get an overview of collection, including user and document counts:
    
    
    1| collections.list = client.collections.list()  
    ---|---  
    2|   
    3| print(f"Collections overview: {collections.list}")  
    4| # {'results': [{'collection_id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Updated Marketing Team', 'description': 'New description for marketing team', 'user_count': 5, 'document_count': 10, ...}, ...]}  
  
### Deleting a Collection

To delete a collection:
    
    
    1| delete_result = client.delete_collection(collection_id)  
    ---|---  
    2|   
    3| print(f"Delete collection result: {delete_result}")  
    4| # {'results': {'message': 'Collection successfully deleted'}}  
  
## Pagination and Filtering

Many of the collection-related methods support pagination and filtering. Here are some examples:
    
    
    1| # List collections with pagination  
    ---|---  
    2| paginated_collection = client.collections.list(offset=10, limit=20)  
    3|   
    4| # Get users in a collection with pagination  
    5| paginated_users = client.collections.list_users(collection_id, offset=5, limit=10)  
    6|   
    7| # Get documents in a collection with pagination  
    8| paginated_docs = client.collections.list_documents(collection_id, offset=0, limit=50)  
    9|   
    10| # Get collections overview with specific collection IDs  
    11| specific_collections.list = client.collections.list(collection_ids=['id1', 'id2', 'id3'])  
  
## Security Considerations

When implementing collection permissions, consider the following security best practices:

  1. **Least Privilege Principle** : Assign the minimum necessary permissions to users and collections.
  2. **Regular Audits** : Periodically review collection memberships and document assignments.
  3. **Access Control** : Ensure that only authorized users (e.g., admins) can perform collection management operations.
  4. **Logging and Monitoring** : Implement comprehensive logging for all collection-related actions.



## Customizing Collection Permissions

While R2R’s current collection system follows a flat hierarchy, you can build more complex permission structures on top of it:

  1. **Custom Roles** : Implement application-level roles within collections (e.g., collection admin, editor, viewer).
  2. **Hierarchical Collections** : Create a hierarchy by establishing parent-child relationships between collections in your application logic.
  3. **Permission Inheritance** : Implement rules for permission inheritance based on collection memberships.



## Troubleshooting

Here are some common issues and their solutions:

  1. **Unable to Create/Modify Collections** : Ensure the user has superuser privileges.
  2. **User Not Seeing Collection Content** : Verify that the user is correctly added to the collection and that documents are properly assigned.
  3. **Performance Issues with Large Collections** : Use pagination when retrieving users or documents in large collections.



## Conclusion

R2R’s collection permissioning system provides a foundation for implementing sophisticated access control in your applications. As the feature set evolves, more advanced capabilities will become available. Stay tuned to the R2R documentation for updates and new features related to collection permissions.

For user authentication and individual user management, refer to the [User Auth Cookbook](/documentation/user-auth). For more advanced use cases or custom implementations, consult the R2R documentation or reach out to the community for support.

Was this page helpful?

YesNo

[Previous](/self-hosting/user-auth)#### [ApplicationLearn how to set up and use the R2R Application for managing your instance.Next](/self-hosting/application)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Quickstart | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * [Overview](/documentation/overview)
    * [Quickstart](/documentation/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * General

    * [Documents](/documentation/documents)
    * [Conversations](/documentation/conversations)
    * [Collections](/documentation/collections)
    * [Graphs](/documentation/graphs)
    * [Prompts](/documentation/prompts)
    * [Users](/documentation/user-auth)
  * Retrieval

    * [Search and RAG](/documentation/search-and-rag)
    * [Agentic RAG](/documentation/retrieval/agentic-rag)
    * [Hybrid Search](/documentation/hybrid-search)
    * [Advanced RAG](/documentation/advanced-rag)
  * Advanced

    * [Deduplication](/documentation/deduplication)
    * [Contextual Enrichment](/documentation/contextual-enrichment)
  * Other

    * SciPhi Cloud




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Additional Features](/documentation/quickstart#additional-features)
  * [Graphs](/documentation/quickstart#graphs)
  * [Users and Collections](/documentation/quickstart#users-and-collections)
  * [Next Steps](/documentation/quickstart#next-steps)



[Getting Started](/documentation/overview)

# Quickstart

Copy page

Getting started with R2R is easy.

[1](/documentation/quickstart#create-an-account)

### Create an Account

Create an account with [SciPhi Cloud](https://app.sciphi.ai/). It’s free!

##### 

For those interested in deploying R2R locally, please [ refer here](/self-hosting/installation/overview).

[2](/documentation/quickstart#install-the-sdk)

### Install the SDK

R2R offers Python and JavaScript SDKs to interact with.

###### Python

###### JavaScript
    
    
    1| pip install r2r  
    ---|---  
  
[3](/documentation/quickstart#environment)

### Environment

After signing into [SciPhi Cloud](https://app.sciphi.ai/), navigate to the homepage and click `Create New Key` (_for the self-hosted quickstart,[refer here](/self-hosting/quickstart)_): ![API Key](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/api_key.png)

Next, set your local environment variable `R2R_API_KEY`. Be sure to include the entire API key ``pk_..`**.**`sk_...``. Alternatively, you may login directly with the client.

[4](/documentation/quickstart#client)

### Client

###### Python

###### JavaScript
    
    
    1| # export R2R_API_KEY=...  
    ---|---  
    2| from r2r import R2RClient  
    3|   
    4| client = R2RClient() # can set remote w/ R2RClient(base_url=...)  
    5|   
    6| # or, alternatively, client.users.login("my@email.com", "my_strong_password")  
  
[5](/documentation/quickstart#ingesting-files)

### Ingesting files

When you ingest files into R2R, the server accepts the task, processes and chunks the file, and generates a summary of the document.

###### Python

###### JavaScript
    
    
    1| client.documents.create_sample(hi_res=True)  
    ---|---  
    2| # to ingest your own document, client.documents.create(file_path="/path/to/file")  
  
Example output:
    
    
    IngestionResponse(message='Document created and ingested successfully.', task_id=None, document_id=UUID('e43864f5-a36f-548e-aacd-6f8d48b30c7f'))  
    ---  
  
[6](/documentation/quickstart#getting-file-status)

### Getting file status

After file ingestion is complete, you can check the status of your documents by listing them.

###### Python

###### JavaScript

###### Curl
    
    
    1| client.documents.list()  
    ---|---  
  
Example output:
    
    
    [  
    ---  
      DocumentResponse(  
        id=UUID('e43864f5-a36f-548e-aacd-6f8d48b30c7f'),   
        collection_ids=[UUID('122fdf6a-e116-546b-a8f6-e4cb2e2c0a09')],   
        owner_id=UUID('2acb499e-8428-543b-bd85-0d9098718220'),   
        document_type=<DocumentType.PDF: 'pdf'>,   
        metadata={'title': 'DeepSeek_R1.pdf', 'version': 'v0'},   
        version='v0',   
        size_in_bytes=1768572,   
        ingestion_status=<IngestionStatus.SUCCESS: 'success'>,   
        extraction_status=<GraphExtractionStatus.PENDING: 'pending'>,   
        created_at=datetime.datetime(2025, 2, 8, 3, 31, 39, 126759, tzinfo=TzInfo(UTC)),   
        updated_at=datetime.datetime(2025, 2, 8, 3, 31, 39, 160114, tzinfo=TzInfo(UTC)),   
        ingestion_attempt_number=None,   
        summary="The document contains a comprehensive overview of DeepSeek-R1, a series of reasoning models developed by DeepSeek-AI, which includes DeepSeek-R1-Zero and DeepSeek-R1. DeepSeek-R1-Zero utilizes large-scale reinforcement learning (RL) without supervised fine-tuning, showcasing impressive reasoning capabilities but facing challenges like readability and language mixing. To enhance performance, DeepSeek-R1 incorporates multi-stage training and cold-start data, achieving results comparable to OpenAI's models on various reasoning tasks. The document details the models' training processes, evaluation results across multiple benchmarks, and the introduction of distilled models that maintain reasoning capabilities while being smaller and more efficient. It also discusses the limitations of current models, such as language mixing and sensitivity to prompts, and outlines future research directions to improve general capabilities and efficiency in software engineering tasks. The findings emphasize the potential of RL in developing reasoning abilities in large language models and the effectiveness of distillation techniques for smaller models.", summary_embedding=None, total_tokens=29673)] total_entries=1  
      ), ...  
    ]  
  
[7](/documentation/quickstart#executing-a-search)

### Executing a search

Perform a search query:

###### Python

###### JavaScript

###### Curl
    
    
    1| client.retrieval.search(  
    ---|---  
    2|   query="What is DeepSeek R1?",  
    3| )  
  
The search query will use basic similarity search to find the most relevant documents. You can use advanced search methods like [hybrid search](/documentation/hybrid-search) or [graph search](/documentation/graphs) depending on your use case.

Example output:
    
    
    AggregateSearchResult(  
    ---  
      chunk_search_results=[  
        ChunkSearchResult(  
          score=0.643,   
          text="Document Title: DeepSeek_R1.pdf  
          Text: could achieve an accuracy of over 70%.  
          DeepSeek-R1 also delivers impressive results on IF-Eval, a benchmark designed to assess a  
          models ability to follow format instructions. These improvements can be linked to the inclusion  
          of instruction-following data during the final stages of supervised fine-tuning (SFT) and RL  
          training. Furthermore, remarkable performance is observed on AlpacaEval2.0 and ArenaHard,  
          indicating DeepSeek-R1s strengths in writing tasks and open-domain question answering. Its  
          significant outperformance of DeepSeek-V3 underscores the generalization benefits of large-scale  
          RL, which not only boosts reasoning capabilities but also improves performance across diverse  
          domains. Moreover, the summary lengths generated by DeepSeek-R1 are concise, with an  
          average of 689 tokens on ArenaHard and 2,218 characters on AlpacaEval 2.0. This indicates that  
          DeepSeek-R1 avoids introducing length bias during GPT-based evaluations, further solidifying  
          its robustness across multiple tasks."  
        ), ...  
      ],  
      graph_search_results=[],  
      web_search_results=[],  
      context_document_results=[]  
    )  
  
[8](/documentation/quickstart#rag)

### RAG

Generate a RAG response:

###### Python

###### JavaScript

###### Curl
    
    
    1| client.retrieval.rag(  
    ---|---  
    2|   query="What is DeepSeek R1?",  
    3| )  
  
Example output:
    
    
    RAGResponse(  
    ---  
      generated_answer='DeepSeek-R1 is a model that demonstrates impressive performance across various tasks, leveraging reinforcement learning (RL) and supervised fine-tuning (SFT) to enhance its capabilities. It excels in writing tasks, open-domain question answering, and benchmarks like IF-Eval, AlpacaEval2.0, and ArenaHard [1], [2]. DeepSeek-R1 outperforms its predecessor, DeepSeek-V3, in several areas, showcasing its strengths in reasoning and generalization across diverse domains [1]. It also achieves competitive results on factual benchmarks like SimpleQA, although it performs worse on the Chinese SimpleQA benchmark due to safety RL constraints [2]. Additionally, DeepSeek-R1 is involved in distillation processes to transfer its reasoning capabilities to smaller models, which perform exceptionally well on benchmarks [4], [6]. The model is optimized for English and Chinese, with plans to address language mixing issues in future updates [8].',   
      search_results=AggregateSearchResult(  
        chunk_search_results=[ChunkSearchResult(score=0.643, text=Document Title: DeepSeek_R1.pdf ...)]  
      ),  
      citations=[Citation(id='cit_3a35e39', object='citation', payload=ChunkSearchResult(score=0.676, text=Document Title: DeepSeek_R1.pdf\n\nText: However, DeepSeek-R1-Zero encounters challenges such as poor readability, and language mixing. To address these issues and further enhance reasoning performance, we introduce DeepSeek-R1, which incorporates a small amount of cold-start data and a multi-stage training pipeline. Specifically, we begin by collecting thousands of cold-start data to fine-tune the DeepSeek-V3-Base model. Following this, we perform reasoning-oriented RL like DeepSeek-R1-Zero. Upon nearing convergence in the RL process, we create new SFT data through rejection sampling on the RL checkpoint, combined with supervised data from DeepSeek-V3 in domains such as writing, factual QA, and self-cognition, and then retrain the DeepSeek-V3-Base model. After fine-tuning with the new data, the checkpoint undergoes an additional RL process, taking into account prompts from all scenarios. After these steps, we obtained a checkpoint referred to as DeepSeek-R1, which achieves performance on par with OpenAI-o1-1217.)), Citation(id='cit_ec89403', object='citation', payload=ChunkSearchResult(score=0.664, text=Document Title: DeepSeek_R1.pdf\n\nText: - We introduce our pipeline to develop DeepSeek-R1. The pipeline incorporates two RL stages aimed at discovering improved reasoning patterns and aligning with human preferences, as well as two SFT stages that serve as the seed for the model's reasoning and non-reasoning capabilities. We believe the pipeline will benefit the industry by creating better models.)), ...],  
      metadata={'id': 'chatcmpl-B0BaZ0vwIa58deI0k8NIuH6pBhngw', 'choices': [{'finish_reason': 'stop', 'index': 0, 'logprobs': None, 'message': {'refusal': None, 'role': 'assistant', 'audio': None, 'function_call': None, 'tool_calls': None}}], 'created': 1739384247, 'model': 'gpt-4o-2024-08-06', 'object': 'chat.completion', 'service_tier': 'default', 'system_fingerprint': 'fp_4691090a87', ...}  
    )  
  
[9](/documentation/quickstart#streaming-rag)

### Streaming RAG

Generate a streaming RAG response:

###### Python

###### JavaScript

###### Curl
    
    
    1| from r2r import (  
    ---|---  
    2|     CitationEvent,  
    3|     FinalAnswerEvent,  
    4|     MessageEvent,  
    5|     SearchResultsEvent,  
    6|     R2RClient,  
    7| )  
    8|   
    9|   
    10| result_stream = client.retrieval.rag(  
    11|     query="What is DeepSeek R1?",  
    12|     search_settings={"limit": 25},  
    13|     rag_generation_config={"stream": True},  
    14| )  
    15|   
    16| # can also do a switch on `type` field  
    17| for event in result_stream:  
    18|     if isinstance(event, SearchResultsEvent):  
    19|         print("Search results:", event.data)  
    20|     elif isinstance(event, MessageEvent):  
    21|         print("Partial message:", event.data.delta)  
    22|     elif isinstance(event, CitationEvent):  
    23|         print("New citation detected:", event.data)  
    24|     elif isinstance(event, FinalAnswerEvent):  
    25|         print("Final answer:", event.data.generated_answer)  
  
Example output:
    
    
    Search results: id='run_1' object='rag.search_results' data={'chunk_search_results': [{'id': '1e40ee7e-2eef-524f-b5c6-1a1910e73ccc', 'document_id': '652075c0-3a43-519f-9625-f581e7605bc5', 'owner_id': '2acb499e-8428-543b-bd85-0d9098718220', 'collection_ids': ['122fdf6a-e116-546b-a8f6-e4cb2e2c0a09'], 'score': 0.7945216641038179, 'text': 'data, achieving strong performance across various tasks. DeepSeek-R1 is more powerful,\nleveraging cold-start data alongside iterative RL fine-tuning. Ultimately ...   
    ---  
    ...  
    Partial message: {'content': [MessageDelta(type='text', text={'value': 'Deep', 'annotations': []})]}  
    Partial message: {'content': [MessageDelta(type='text', text={'value': 'Seek', 'annotations': []})]}  
    Partial message: {'content': [MessageDelta(type='text', text={'value': '-R', 'annotations': []})]}  
    ...  
    New Citation Detected: 'cit_3a35e39'  
    ...  
    Final answer: DeepSeek-R1 is a large language model developed by the DeepSeek-AI research team. It is a reasoning model that has been trained using multi-stage training and cold-start data before reinforcement learning (RL). The model demonstrates superior performance on various benchmarks, including MMLU, MMLU-Pro, GPQA Diamond, and FRAMES, particularly in STEM-related questions. ...  
  
[10](/documentation/quickstart#streaming-agentic-rag)

### Streaming Agentic RAG

R2R offers a powerful `agentic` retrieval mode that performs in-depth analysis of documents through iterative research and reasoning. This mode can leverage a variety of tools to thoroughly investigate your data and the web:

###### Python

###### JavaScript
    
    
    1| from r2r import (  
    ---|---  
    2|     ThinkingEvent,  
    3|     ToolCallEvent,  
    4|     ToolResultEvent,  
    5|     CitationEvent,  
    6|     FinalAnswerEvent,  
    7|     MessageEvent,  
    8|     R2RClient,  
    9| )  
    10|   
    11| results = client.retrieval.agent(  
    12|     message={"role": "user", "content": "What does deepseek r1 imply for the future of AI?"},  
    13|     rag_generation_config={  
    14|         "model": "anthropic/claude-3-7-sonnet-20250219",  
    15|         "extended_thinking": True,  
    16|         "thinking_budget": 4096,  
    17|         "temperature": 1,  
    18|         "top_p": None,  
    19|         "max_tokens_to_sample": 16000,  
    20|         "stream": True  
    21|     },  
    22| )  
    23|   
    24| # Process the streaming events  
    25| for event in results:  
    26|     if isinstance(event, ThinkingEvent):  
    27|         print(f"🧠 Thinking: {event.data.delta.content[0].payload.value}")  
    28|     elif isinstance(event, ToolCallEvent):  
    29|         print(f"🔧 Tool call: {event.data.name}({event.data.arguments})")  
    30|     elif isinstance(event, ToolResultEvent):  
    31|         print(f"📊 Tool result: {event.data.content[:60]}...")  
    32|     elif isinstance(event, CitationEvent):  
    33|         print(f"📑 Citation: {event.data}")  
    34|     elif isinstance(event, MessageEvent):  
    35|         print(f"💬 Message: {event.data.delta.content[0].payload.value}")  
    36|     elif isinstance(event, FinalAnswerEvent):  
    37|         print(f"✅ Final answer: {event.data.generated_answer[:100]}...")  
    38|         print(f"   Citations: {len(event.data.citations)} sources referenced")  
  
Example of streaming output:
    
    
    🧠 Thinking: Analyzing the query about DeepSeek R1 implications...  
    ---  
    🔧 Tool call: search_file_knowledge({"query":"DeepSeek R1 capabilities advancements"})  
    📊 Tool result: DeepSeek-R1 is a reasoning-focused LLM that uses reinforcement learning...  
    🧠 Thinking: The search provides valuable information about DeepSeek R1's capabilities  
    🧠 Thinking: Need more specific information about its performance in reasoning tasks  
    🔧 Tool call: search_file_knowledge({"query":"DeepSeek R1 reasoning benchmarks performance"})  
    📊 Tool result: DeepSeek-R1 achieves strong results on reasoning benchmarks including MMLU...  
    📑 Citation: cit_54c45c8  
    🧠 Thinking: Now I need to understand the implications for AI development  
    🔧 Tool call: web_search({"query":"AI reasoning capabilities future development"})  
    📊 Tool result: Advanced reasoning capabilities are considered a key milestone toward...  
    📑 Citation: cit_d1152e7  
    💬 Message: DeepSeek-R1 has several important implications for the future of AI development:  
    💬 Message: 1. **Reinforcement Learning as a Key Approach**: DeepSeek-R1's success demonstrates...  
    📑 Citation: cit_eb5ba04  
    💬 Message: 2. **Efficiency Through Distillation**: The model shows that reasoning capabilities...  
    ✅ Final answer: DeepSeek-R1 has several important implications for the future of AI development: 1. Reinforcement Learning...  
      Citations: 3 sources referenced      
  
## Additional Features

R2R offers the additional features below to enhance your document management and user experience.

### Graphs

R2R provides powerful entity and relationshipo extraction capabilities that enhance document understanding and retrieval. These can leveraged to construct knowledge graphs inside R2R. The system can automatically identify entities, build relationships between them, and create enriched knowledge graphs from your document collection.

[Knowledge GraphsAutomatically extract entities and relationships from documents to form knowledge graphs.](/documentation/graphs)

### Users and Collections

R2R provides a complete set of user authentication and management features, allowing you to implement secure and feature-rich authentication systems or integrate with your preferred authentication provider. Further, collections exist to enable efficient access control and organization of users and documents.

[User Auth CookbookLearn how to implement user registration, login, email verification, and more using R2R’s built-in authentication capabilities.](/documentation/user-auth)[Collections CookbookDiscover how to create, manage, and utilize collections in R2R for granular access control and document organization.](/documentation/collections)

## Next Steps

Now that you have a basic understanding of R2R’s core features, you can explore more advanced topics:

  * Dive into [document ingestion](/documentation/documents) and [the document reference](/api-and-sdks/documents/documents).
  * Learn about [search and RAG](/documentation/hybrid-search) and the [retrieval reference](/api-and-sdks/retrieval/retrieval).
  * Try advanced techniques like [knowledge-graphs](/documentation/graphs) and refer to the [graph reference](/api-and-sdks/graphs/graphs).
  * Learn about [user authentication](/documentation/user-auth) to secure your application permissions and [the users API reference](/api-and-sdks/users/users).
  * Organize your documents using [collections](/api-and-sdks/collections/collections) for granular access control.



Was this page helpful?

YesNo

[Previous](/documentation/overview)#### [WalkthroughA detailed step-by-step cookbook of the core features provided by R2R.Next](/documentation/walkthrough)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Knowledge Graphs | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Data Processing and Retrieval

    * [Ingestion](/cookbooks/ingestion)
    * [Knowledge Graphs](/cookbooks/graphs)
    * [User-Defined Agent Tools](/cookbooks/custom-tools)
  * System Operations

    * [Email Verification](/cookbooks/email)
    * [Maintenance & Scaling](/cookbooks/maintenance)
    * [Orchestration](/cookbooks/orchestration)
  * Other

    * [Local LLMs](/cookbooks/local-llms)
    * [Structured Output](/cookbooks/structured-output)
    * [MCP](/cookbooks/other/mcp)
    * [Web Development](/cookbooks/web-dev)
    * [Evals](/cookbooks/other/evals)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Overview](/cookbooks/graphs#overview)



[Data Processing and Retrieval](/cookbooks/ingestion)

# Knowledge Graphs

Copy page

Building and managing graphs through collections

## Overview

R2R allows you to build and analyze knowledge graphs from your documents through a collection-based architecture. The system extracts entities and relationships from documents, enabling richer search capabilities that understand connections between information.

The process works in several key stages:

  * Documents are first ingested and entities/relationships are extracted
  * Collections serve as containers for documents and their corresponding graphs
  * Extracted information is pulled into the collection’s graph
  * Communities can be built to identify higher-level concepts
  * The resulting graph enhances search with relationship-aware queries



Collections in R2R are flexible containers that support multiple documents and provide features for access control and graph management. A document can belong to multiple collections, allowing for different organizational schemes and sharing patterns.

The resulting knowledge graphs improve search accuracy by understanding relationships between concepts rather than just performing traditional document search.

[1](/cookbooks/graphs#ingestion-and-extraction)

### Ingestion and Extraction

Before we can extract entities and relationships from a document, we must ingest a file. After we’ve successfully ingested a file, we can `extract` the entities and relationships from document.

In the following script, we fetch _The Gift of the Magi_ by O. Henry and ingest it our R2R server. We then begin the extraction process, which may take a few minutes to run.

###### Python
    
    
    1| import requests  
    ---|---  
    2| from r2r import R2RClient  
    3| import tempfile  
    4| import os  
    5|   
    6| # Set up the client  
    7| client = R2RClient("http://localhost:7272")  
    8|   
    9| # Fetch the text file  
    10| url = "https://www.gutenberg.org/cache/epub/7256/pg7256.txt"  
    11| response = requests.get(url)  
    12|   
    13| # Create a temporary file  
    14| temp_dir = tempfile.gettempdir()  
    15| temp_file_path = os.path.join(temp_dir, "gift_of_the_magi.txt")  
    16| with open(temp_file_path, 'w') as temp_file:  
    17|     temp_file.write(response.text)  
    18|   
    19| # Ingest the file  
    20| ingest_response = client.documents.create(file_path=temp_file_path)  
    21| document_id = ingest_response["results"]["document_id"]  
    22|   
    23| # Extract entities and relationships  
    24| extract_response = client.documents.extract(document_id)  
    25|   
    26| # View extracted knowledge  
    27| entities = client.documents.list_entities(document_id)  
    28| relationships = client.documents.list_relationships(document_id)  
    29|   
    30| # Clean up the temporary file  
    31| os.unlink(temp_file_path)  
  
As this script runs, we see indications of successful ingestion and extraction.

###### Ingestion

###### Entities

![Successful ingestion and extraction in the R2R dashboard.](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/cookbooks/graphs/document_table_success.png)

Both ingestion and extraction were successful, as seen in the R2R Dashboard

[2](/cookbooks/graphs#deduplication)

### Deduplication

If you would like to deduplicate the extracted entities, you can run the following method. To learn more about deduplication, view our [deduplication documentation here](/documentation/deduplication).

###### Python
    
    
    1| from r2r import R2RClient  
    ---|---  
    2|   
    3| # Set up the client  
    4| client = R2RClient("http://localhost:7272")  
    5|   
    6| client.documents.deduplicate("20e29a97-c53c-506d-b89c-1f5346befc58")  
  
While the exact number of extracted entities and relationships will differ across models, this particular document produces approximately 120 entities, with only 20 distinct entities.

[3](/cookbooks/graphs#managing-collections)

### Managing Collections

Graphs are built within a collection, allowing for us to add many documents to a graph, and to share our graphs with other users. When we ingested the file above, it was added into our default collection.

Each collection has a description which is used in the graph creation process. This can be set by the user, or generated using an LLM.

###### Python
    
    
    1| from r2r import R2RClient  
    ---|---  
    2|   
    3| # Set up the client  
    4| client = R2RClient("http://localhost:7272")  
    5|   
    6| # Update the description of the default collection  
    7| collection_id = "122fdf6a-e116-546b-a8f6-e4cb2e2c0a09"  
    8| update_result = client.collections.update(  
    9|     id=collection_id,  
    10|     generate_description=True, # LLM generated  
    11| )  
  
![The resulting description.](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/cookbooks/graphs/collection_description.png)

The LLM generated description for our collection

[4](/cookbooks/graphs#pulling-extractions-into-the-graph)

### Pulling Extractions into the Graph

Our graph will not contain the extractions from our documents until we `pull` them into the graph. This gives developers more granular control over the creation and management of graphs.

Recall that we already extracted the entities and relationships for the graph; this means that we can `pull` a document into many graphs without having to rerun the extraction process.

###### Python
    
    
    1| from r2r import R2RClient  
    ---|---  
    2|   
    3| # Set up the client  
    4| client = R2RClient("http://localhost:7272")  
    5|   
    6| # Pull the extractions from all docments into the default collection  
    7| collection_id = "122fdf6a-e116-546b-a8f6-e4cb2e2c0a09"  
    8| client.graphs.pull(  
    9|     collection_id=collection_id  
    10| )  
  
As soon as we `pull` the extractions into the graph, we can begin using the graph in our searches. We can confirm that the entities and relationships were pulled into the collection, as well.

###### Entities

###### Entity Visualization

![Successful ingestion and extraction in the R2R dashboard.](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/cookbooks/graphs/entity_view_collection.png)

Entities are `pulled` in from the document to the collection

[5](/cookbooks/graphs#building-communities)

### Building Communities

To further enhance our graph we can build communities, which clusters over the entities and relationships inside our graph. This allows us to capture higher-level concepts that exist within our data.

###### Python
    
    
    1| from r2r import R2RClient  
    ---|---  
    2|   
    3| # Set up the client  
    4| client = R2RClient("http://localhost:7272")  
    5|   
    6| # Build the communities for the default collection  
    7| collection_id = "122fdf6a-e116-546b-a8f6-e4cb2e2c0a09"  
    8| client.graphs.build(  
    9|     collection_id=collection_id  
    10| )  
  
We can see that the resulting communities capture overall themes and concepts within the story.

![The communities generated for the collection.](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/cookbooks/graphs/communities.png)

The resulting communities, generated from the clustering process

[6](/cookbooks/graphs#graph-search)

### Graph Search

Now that we have built our graph we can query over it. Good questions for graphs might require deep understanding of relationships and ideas that span across multiple documents.

###### Python
    
    
    1| from r2r import R2RClient  
    ---|---  
    2|   
    3| # Set up the client  
    4| client = R2RClient("http://localhost:7272")  
    5|   
    6| results = client.retrieval.search("""  
    7|     What items did Della and Jim each originally own,  
    8|     what did they do with those items, and what did they  
    9|     ultimately give each other?  
    10|     """,  
    11|     search_settings={  
    12|         "graph_settings": {"enabled": True},  
    13|     }  
    14| )  
  
![Performing a searhc over the graph.](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/cookbooks/graphs/graph_search.png)

Performing a multi-hop query over the graph

Was this page helpful?

YesNo

[Previous](/cookbooks/ingestion)#### [User-Defined Agent ToolsDefine custom tools for the RAG AgentNext](/cookbooks/custom-tools)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Agentic RAG | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * [Overview](/documentation/overview)
    * [Quickstart](/documentation/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * General

    * [Documents](/documentation/documents)
    * [Conversations](/documentation/conversations)
    * [Collections](/documentation/collections)
    * [Graphs](/documentation/graphs)
    * [Prompts](/documentation/prompts)
    * [Users](/documentation/user-auth)
  * Retrieval

    * [Search and RAG](/documentation/search-and-rag)
    * [Agentic RAG](/documentation/retrieval/agentic-rag)
    * [Hybrid Search](/documentation/hybrid-search)
    * [Advanced RAG](/documentation/advanced-rag)
  * Advanced

    * [Deduplication](/documentation/deduplication)
    * [Contextual Enrichment](/documentation/contextual-enrichment)
  * Other

    * SciPhi Cloud




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Key Features](/documentation/retrieval/agentic-rag#key-features)
  * [Available Modes](/documentation/retrieval/agentic-rag#available-modes)
  * [RAG Mode (Default)](/documentation/retrieval/agentic-rag#rag-mode-default)
  * [Research Mode](/documentation/retrieval/agentic-rag#research-mode)
  * [Available Tools](/documentation/retrieval/agentic-rag#available-tools)
  * [RAG Tools](/documentation/retrieval/agentic-rag#rag-tools)
  * [Research Tools](/documentation/retrieval/agentic-rag#research-tools)
  * [Basic Usage](/documentation/retrieval/agentic-rag#basic-usage)
  * [Using Research Mode](/documentation/retrieval/agentic-rag#using-research-mode)
  * [Customizing the Agent](/documentation/retrieval/agentic-rag#customizing-the-agent)
  * [Tool Selection](/documentation/retrieval/agentic-rag#tool-selection)
  * [Search Settings Propagation](/documentation/retrieval/agentic-rag#search-settings-propagation)
  * [Model Selection and Parameters](/documentation/retrieval/agentic-rag#model-selection-and-parameters)
  * [Multi-Turn Conversations](/documentation/retrieval/agentic-rag#multi-turn-conversations)
  * [Performance Considerations](/documentation/retrieval/agentic-rag#performance-considerations)
  * [Response Time Management](/documentation/retrieval/agentic-rag#response-time-management)
  * [Handling Large Context](/documentation/retrieval/agentic-rag#handling-large-context)
  * [How Tools Work (Under the Hood)](/documentation/retrieval/agentic-rag#how-tools-work-under-the-hood)
  * [RAG Mode Tools](/documentation/retrieval/agentic-rag#rag-mode-tools)
  * [Research Mode Tools](/documentation/retrieval/agentic-rag#research-mode-tools)
  * [Conclusion](/documentation/retrieval/agentic-rag#conclusion)



[Retrieval](/documentation/search-and-rag)

# Agentic RAG

Copy page

R2R’s **Agentic RAG** orchestrates multi-step reasoning with Retrieval-Augmented Generation (RAG). By pairing large language models with advanced retrieval and tool integrations, the agent can fetch relevant data from the internet, your documents and knowledge graphs, reason over it, and produce robust, context-aware answers.

##### 

Agentic RAG (also called Deep Research) is an extension of R2R’s basic retrieval functionality. If you are new to R2R, we suggest starting with the [Quickstart](/documentation/quickstart) and [Search & RAG](/documentation/search-and-rag) docs first.

## Key Features

Multi-Step Reasoning

The agent can chain multiple actions, like searching documents or referencing conversation history, before generating its final response.

Retrieval Augmentation

Integrates with R2R’s vector, full-text, or hybrid search to gather the most relevant context for each query.

Conversation Context

Maintain dialogue across multiple turns by including `conversation_id` in each request.

Tool Usage

Dynamically invoke tools at runtime to gather and analyze information from various sources.

## Available Modes

The Agentic RAG system offers two primary operating modes:

### RAG Mode (Default)

Standard retrieval-augmented generation for answering questions based on your knowledge base:

  * Semantic and hybrid search capabilities
  * Document-level and chunk-level content retrieval
  * Optional web search integrations, leveraging Serper and Firecrawl
  * Source citation and evidence-based responses



### Research Mode

Advanced capabilities for deep analysis, reasoning, and computation:

  * All RAG mode capabilities
  * A dedicated reasoning system for complex problem-solving
  * Critique capabilities to identify potential biases or logical fallacies
  * Python execution for computational analysis
  * Multi-step reasoning for deeper exploration of topics



## Available Tools

### RAG Tools

The agent can use the following tools in RAG mode:

Tool Name| Description| Dependencies  
---|---|---  
`search_file_knowledge`| Semantic/hybrid search on your ingested documents using R2R’s search capabilities| None  
`search_file_descriptions`| Search over file-level metadata (titles, doc-level descriptions)| None  
`get_file_content`| Fetch entire documents or chunk structures for deeper analysis| None  
`web_search`| Query external search APIs for up-to-date information| Requires `SERPER_API_KEY` environment variable ([serper.dev](https://serper.dev/))  
`web_scrape`| Scrape and extract content from specific web pages| Requires `FIRECRAWL_API_KEY` environment variable ([firecrawl.dev](https://www.firecrawl.dev/))  
  
### Research Tools

The agent can use the following tools in Research mode:

Tool Name| Description| Dependencies  
---|---|---  
`rag`| Leverage the underlying RAG agent to perform information retrieval and synthesis| None  
`reasoning`| Call a dedicated model for complex analytical thinking| None  
`critique`| Analyze conversation history to identify flaws, biases, and alternative approaches| None  
`python_executor`| Execute Python code for complex calculations and analysis| None  
  
## Basic Usage

Below are examples of how to use the agent for both single-turn queries and multi-turn conversations.

###### Python

###### JavaScript

###### Curl
    
    
    1| from r2r import R2RClient  
    ---|---  
    2| from r2r import (  
    3|     ThinkingEvent,  
    4|     ToolCallEvent,  
    5|     ToolResultEvent,  
    6|     CitationEvent,  
    7|     MessageEvent,  
    8|     FinalAnswerEvent,  
    9| )  
    10|   
    11| # when using auth, do client.users.login(...)  
    12|   
    13| # Basic RAG mode with streaming  
    14| response = client.retrieval.agent(  
    15|     message={  
    16|         "role": "user",  
    17|         "content": "What does DeepSeek R1 imply for the future of AI?"  
    18|     },  
    19|     rag_generation_config={  
    20|         "model": "anthropic/claude-3-7-sonnet-20250219",  
    21|         "extended_thinking": True,  
    22|         "thinking_budget": 4096,  
    23|         "temperature": 1,  
    24|         "top_p": None,  
    25|         "max_tokens_to_sample": 16000,  
    26|         "stream": True  
    27|     },  
    28|     rag_tools=["search_file_knowledge", "get_file_content"],  
    29|     mode="rag"  
    30| )  
    31|   
    32| # Improved streaming event handling  
    33| current_event_type = None  
    34| for event in response:  
    35|     # Check if the event type has changed  
    36|     event_type = type(event)  
    37|     if event_type != current_event_type:  
    38|         current_event_type = event_type  
    39|         print() # Add newline before new event type  
    40|   
    41|         # Print emoji based on the new event type  
    42|         if isinstance(event, ThinkingEvent):  
    43|             print(f"\n🧠 Thinking: ", end="", flush=True)  
    44|         elif isinstance(event, ToolCallEvent):  
    45|             print(f"\n🔧 Tool call: ", end="", flush=True)  
    46|         elif isinstance(event, ToolResultEvent):  
    47|             print(f"\n📊 Tool result: ", end="", flush=True)  
    48|         elif isinstance(event, CitationEvent):  
    49|             print(f"\n📑 Citation: ", end="", flush=True)  
    50|         elif isinstance(event, MessageEvent):  
    51|             print(f"\n💬 Message: ", end="", flush=True)  
    52|         elif isinstance(event, FinalAnswerEvent):  
    53|             print(f"\n✅ Final answer: ", end="", flush=True)  
    54|   
    55|     # Print the content without the emoji  
    56|     if isinstance(event, ThinkingEvent):  
    57|         print(f"{event.data.delta.content[0].payload.value}", end="", flush=True)  
    58|     elif isinstance(event, ToolCallEvent):  
    59|         print(f"{event.data.name}({event.data.arguments})")  
    60|     elif isinstance(event, ToolResultEvent):  
    61|         print(f"{event.data.content[:60]}...")  
    62|     elif isinstance(event, CitationEvent):  
    63|         print(f"{event.data}")  
    64|     elif isinstance(event, MessageEvent):  
    65|         print(f"{event.data.delta.content[0].payload.value}", end="", flush=True)  
    66|     elif isinstance(event, FinalAnswerEvent):  
    67|         print(f"{event.data.generated_answer[:100]}...")  
    68|         print(f"   Citations: {len(event.data.citations)} sources referenced")  
  
## Using Research Mode

Research mode provides more advanced reasoning capabilities for complex questions:

###### Python

###### JavaScript
    
    
    1| # Research mode with all available tools  
    ---|---  
    2| response = client.retrieval.agent(  
    3|     message={  
    4|         "role": "user",   
    5|         "content": "Analyze the philosophical implications of DeepSeek R1 for the future of AI reasoning"  
    6|     },  
    7|     research_generation_config={  
    8|         "model": "anthropic/claude-3-opus-20240229",  
    9|         "extended_thinking": True,  
    10|         "thinking_budget": 8192,  
    11|         "temperature": 0.2,  
    12|         "max_tokens_to_sample": 32000,  
    13|         "stream": True  
    14|     },  
    15|     research_tools=["rag", "reasoning", "critique", "python_executor"],  
    16|     mode="research"  
    17| )  
    18|   
    19| # Process streaming events as shown in the previous example  
    20| # ...  
    21|   
    22| # Research mode with computational focus  
    23| # This example solves a mathematical problem using the python_executor tool  
    24| compute_response = client.retrieval.agent(  
    25|     message={  
    26|         "role": "user",   
    27|         "content": "Calculate the factorial of 15 multiplied by 32. Show your work."  
    28|     },  
    29|     research_generation_config={  
    30|         "model": "anthropic/claude-3-opus-20240229",  
    31|         "max_tokens_to_sample": 1000,  
    32|         "stream": False  
    33|     },  
    34|     research_tools=["python_executor"],  
    35|     mode="research"  
    36| )  
    37|   
    38| print(f"Final answer: {compute_response.results.messages[-1].content}")  
  
## Customizing the Agent

### Tool Selection

You can customize which tools the agent has access to:
    
    
    1| # RAG mode with web capabilities  
    ---|---  
    2| response = client.retrieval.agent(  
    3|     message={"role": "user", "content": "What are the latest developments in AI safety?"},  
    4|     rag_tools=["search_file_knowledge", "get_file_content", "web_search", "web_scrape"],  
    5|     mode="rag"  
    6| )  
    7|   
    8| # Research mode with limited tools  
    9| response = client.retrieval.agent(  
    10|     message={"role": "user", "content": "Analyze the complexity of this algorithm"},  
    11|     research_tools=["reasoning", "python_executor"],  # Only reasoning and code execution  
    12|     mode="research"  
    13| )  
  
### Search Settings Propagation

Any search settings passed to the agent will propagate to downstream searches. This includes:

  * Filters to restrict document sources
  * Limits on the number of results
  * Hybrid search configuration
  * Collection restrictions


    
    
    1| # Using search settings with the agent  
    ---|---  
    2| response = client.retrieval.agent(  
    3|     message={"role": "user", "content": "Summarize our Q1 financial results"},  
    4|     search_settings={  
    5|         "use_semantic_search": True,  
    6|         "filters": {"collection_ids": {"$overlap": ["e43864f5-..."]}},  
    7|         "limit": 25  
    8|     },  
    9|     rag_tools=["search_file_knowledge", "get_file_content"],  
    10|     mode="rag"  
    11| )  
  
### Model Selection and Parameters

You can customize the agent’s behavior by selecting different models and adjusting generation parameters:
    
    
    1| # Using a specific model with custom parameters  
    ---|---  
    2| response = client.retrieval.agent(  
    3|     message={"role": "user", "content": "Write a concise summary of DeepSeek R1's capabilities"},  
    4|     rag_generation_config={  
    5|         "model": "anthropic/claude-3-haiku-20240307",  # Faster model for simpler tasks  
    6|         "temperature": 0.3,                           # Lower temperature for more deterministic output  
    7|         "max_tokens_to_sample": 500,                  # Limit response length  
    8|         "stream": False                               # Non-streaming for simpler use cases  
    9|     },  
    10|     mode="rag"  
    11| )  
  
## Multi-Turn Conversations

You can maintain context across multiple turns using `conversation_id`. The agent will remember previous interactions and build upon them in subsequent responses.

###### Python

###### JavaScript
    
    
    1| # Create a new conversation  
    ---|---  
    2| conversation = client.conversations.create()  
    3| conversation_id = conversation.results.id  
    4|   
    5| # First turn  
    6| first_response = client.retrieval.agent(  
    7|     message={"role": "user", "content": "What does DeepSeek R1 imply for the future of AI?"},  
    8|     rag_generation_config={  
    9|         "model": "anthropic/claude-3-7-sonnet-20250219",  
    10|         "temperature": 0.7,  
    11|         "max_tokens_to_sample": 1000,  
    12|         "stream": False  
    13|     },  
    14|     conversation_id=conversation_id,  
    15|     mode="rag"  
    16| )  
    17| print(f"First response: {first_response.results.messages[-1].content[:100]}...")  
    18|   
    19| # Follow-up query in the same conversation  
    20| follow_up_response = client.retrieval.agent(  
    21|     message={"role": "user", "content": "How does it compare to other reasoning models?"},  
    22|     rag_generation_config={  
    23|         "model": "anthropic/claude-3-7-sonnet-20250219",  
    24|         "temperature": 0.7,  
    25|         "max_tokens_to_sample": 1000,  
    26|         "stream": False  
    27|     },  
    28|     conversation_id=conversation_id,  
    29|     mode="rag"  
    30| )  
    31| print(f"Follow-up response: {follow_up_response.results.messages[-1].content[:100]}...")  
    32|   
    33| # The agent maintains context, so it knows "it" refers to DeepSeek R1  
  
## Performance Considerations

Based on our integration testing, here are some considerations to optimize your agent usage:

### Response Time Management

Response times vary based on the complexity of the query, the number of tools used, and the length of the requested output:
    
    
    1| # For time-sensitive applications, consider:  
    ---|---  
    2| # 1. Using a smaller max_tokens value  
    3| # 2. Selecting faster models like claude-3-haiku  
    4| # 3. Avoiding unnecessary tools  
    5|   
    6| fast_response = client.retrieval.agent(  
    7|     message={"role": "user", "content": "Give me a quick overview of DeepSeek R1"},  
    8|     rag_generation_config={  
    9|         "model": "anthropic/claude-3-haiku-20240307",  # Faster model  
    10|         "max_tokens_to_sample": 200,                   # Limited output  
    11|         "stream": True                                 # Stream for perceived responsiveness  
    12|     },  
    13|     rag_tools=["search_file_knowledge"],              # Minimal tools  
    14|     mode="rag"  
    15| )  
  
### Handling Large Context

The agent can process large document contexts efficiently, but performance can be improved by using appropriate filters:
    
    
    1| # When working with large document collections, use filters to narrow results  
    ---|---  
    2| filtered_response = client.retrieval.agent(  
    3|     message={"role": "user", "content": "Summarize key points from our AI ethics documentation"},  
    4|     search_settings={  
    5|         "filters": {  
    6|             "$and": [  
    7|                 {"document_type": {"$eq": "pdf"}},  
    8|                 {"metadata.category": {"$eq": "ethics"}},  
    9|                 {"metadata.year": {"$gt": 2023}}  
    10|             ]  
    11|         },  
    12|         "limit": 10  # Limit number of chunks returned  
    13|     },  
    14|     rag_generation_config={  
    15|         "max_tokens_to_sample": 500,  
    16|         "stream": True  
    17|     },  
    18|     mode="rag"  
    19| )  
  
## How Tools Work (Under the Hood)

R2R’s Agentic RAG leverages a powerful toolset to conduct comprehensive research:

### RAG Mode Tools

  * **search_file_knowledge** : Looks up relevant text chunks and knowledge graph data from your ingested documents using semantic and hybrid search capabilities.
  * **search_file_descriptions** : Searches over file-level metadata (titles, doc-level descriptions) rather than chunk content.
  * **get_file_content** : Fetches entire documents or their chunk structures for deeper analysis when the agent needs more comprehensive context.
  * **web_search** : Queries external search APIs (like Serper or Google) for live, up-to-date information from the internet. Requires a `SERPER_API_KEY` environment variable.
  * **web_scrape** : Uses Firecrawl to extract content from specific web pages for in-depth analysis. Requires a `FIRECRAWL_API_KEY` environment variable.



### Research Mode Tools

  * **rag** : A specialized research tool that utilizes the underlying RAG agent to perform comprehensive information retrieval and synthesis across your data sources.
  * **python_executor** : Executes Python code for complex calculations, statistical operations, and algorithmic implementations, giving the agent computational capabilities.
  * **reasoning** : Allows the research agent to call a dedicated model as an external module for complex analytical thinking.
  * **critique** : Analyzes conversation history to identify potential flaws, biases, and alternative approaches to improve research rigor.



The Agent is built on a sophisticated architecture that combines these tools with streaming capabilities and flexible response formats. It can decide which tools to use based on the query requirements and can dynamically invoke them during the research process.

## Conclusion

Agentic RAG provides a powerful approach to retrieval-augmented generation. By combining **advanced search** , **multi-step reasoning** , **conversation context** , and **dynamic tool usage** , the agent helps you build sophisticated Q&A or research solutions on your R2R-ingested data.

**Next Steps**

  * **Ingest** your content using [Documents](/documentation/documents).
  * Explore advanced retrieval in [Hybrid Search](/documentation/hybrid-search).
  * Enhance understanding with [Knowledge Graphs](/documentation/graphs).
  * Manage multi-turn chat with [Conversations](/documentation/conversations).
  * Scale up your solution with the [API & SDKs](/api-and-sdks).



Was this page helpful?

YesNo

[Previous](/documentation/search-and-rag)#### [Hybrid SearchCombines chunk and full text search in one query for more relevant resultsNext](/documentation/hybrid-search)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# R2R Installation | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * Installation

    * [Quickstart](/self-hosting/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * Configuration Files

    * [Overview](/self-hosting/configuration/overview)
    * [Database](/self-hosting/configuration/database)
    * [File Storage](/self-hosting/configuration/file-storage)
    * [Embedding](/self-hosting/configuration/embedding)
    * [LLMs](/self-hosting/configuration/llm)
    * [Email](/self-hosting/configuration/email)
    * [Crypto](/self-hosting/configuration/crypto)
    * [Auth](/self-hosting/configuration/auth)
    * [Scheduler](/self-hosting/configuration/scheduler)
    * [Orchestration](/self-hosting/configuration/orchestration)
    * [Agent](/self-hosting/configuration/agent)
    * [Ingestion](/self-hosting/configuration/ingestion)
  * Retrieval and generation

    * [Overview](/self-hosting/configuration/retrieval/overview)
    * [RAG](/self-hosting/configuration/retrieval/rag)
    * [Graphs](/self-hosting/configuration/knowledge-graph/overview)
    * [Prompts](/self-hosting/configuration/retrieval/prompts)
  * System

    * [Local LLMs](/self-hosting/local-rag)
  * Deployment

    * [Introduction](/self-hosting/deployment/introduction)
    * Cloud Providers

  * Users

    * [User Auth](/self-hosting/user-auth)
    * [Collections](/self-hosting/collections)
    * [Application](/self-hosting/application)
  * Other

    * Telemetry




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Choose Your System](/self-hosting/installation/overview#choose-your-system)



[Getting Started](/self-hosting/installation/overview)[Installation](/self-hosting/installation/overview)

# R2R Installation

Copy page

Welcome to the R2R self-hosting installation guide. For those interested in a managed cloud solution, [refer to the quickstart here](/documentation/quickstart).

R2R offers powerful features for your RAG applications, including:

  * **Flexibility** : Run with cloud-based LLMs or entirely on your local machine
  * **State-of-the-Art Tech** : Advanced RAG techniques like [hybrid search](/documentation/search-and-rag), [graphs](/cookbooks/graphs), [advanced RAG](/documentation/advanced-rag), and [agentic RAG](/documentation/retrieval/agentic-rag).
  * **Auth & Orchestration**: Production must-haves like [auth](/documentation/user-auth) and [orchestration](/cookbooks/orchestration).



## Choose Your System

[R2R LightA lightweight version of R2R, **perfect for quick prototyping and simpler applications**. Some advanced features, like orchestration may not be available.](/self-hosting/installation/light)[R2RThe full-featured R2R system, ideal **for advanced use cases and production deployments**. Includes all components and capabilities, such as **Hatchet** for orchestration and **Unstructured** for parsing.](/self-hosting/installation/full)

Choose the system that best aligns with your requirements and proceed with the installation guide.

Was this page helpful?

YesNo

#### [R2R Light InstallationNext](/self-hosting/installation/light)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# More about RAG | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  *     * [Introduction](/introduction)
    * [System](/introduction/system)
    * [What's New](/introduction/whats-new)
  * Guides

    * [What is R2R?](/introduction/what-is-r2r)
    * [More about RAG](/introduction/rag)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [What is RAG?](/introduction/rag#what-is-rag)
  * [Set up RAG with R2R](/introduction/rag#set-up-rag-with-r2r)
  * [Configure RAG settings](/introduction/rag#configure-rag-settings)
  * [How RAG works in R2R](/introduction/rag#how-rag-works-in-r2r)
  * [Best Practices](/introduction/rag#best-practices)



[Guides](/introduction/what-is-r2r)

# More about RAG

Copy page

**On this page**

  1. Before you begin
  2. What is RAG?
  3. Set up RAG with R2R
  4. Configure RAG settings
  5. How RAG works in R2R



RAG (Retrieval-Augmented Generation) combines the power of large language models with precise information retrieval from your own documents. When users ask questions, RAG first retrieves relevant information from your document collection, then uses this context to generate accurate, contextual responses. This ensures AI responses are both relevant and grounded in your specific knowledge base.

**Before you begin**

RAG in R2R has the following requirements:

  * A running R2R instance (local or deployed)
  * Access to an LLM provider (OpenAI, Anthropic, or local models)
  * Documents ingested into your R2R system
  * Basic configuration for document processing and embedding generation



## What is RAG?

RAG operates in three main steps:

  1. **Retrieval** : Finding relevant information from your documents
  2. **Augmentation** : Adding this information as context for the AI
  3. **Generation** : Creating responses using both the context and the AI’s knowledge



Benefits over traditional LLM applications:

  * More accurate responses based on your specific documents
  * Reduced hallucination by grounding answers in real content
  * Ability to work with proprietary or recent information
  * Better control over AI outputs



## Set up RAG with R2R

To start using RAG in R2R:

  1. Install and start R2R:


    
    
    1| pip install r2r  
    ---|---  
    2| r2r serve --docker  
  
  2. Ingest your documents:


    
    
    1| r2r documents create --file-paths /path/to/your/documents  
    ---|---  
  
  3. Test basic RAG functionality:


    
    
    1| r2r retrieval rag --query="your question here"  
    ---|---  
  
## Configure RAG settings

R2R offers several ways to customize RAG behavior:

  1. **Retrieval Settings** :


    
    
    1| # Using hybrid search (combines semantic and keyword search)  
    ---|---  
    2| client.retrieval.rag(  
    3|     query="your question",  
    4|     vector_search_settings={"use_hybrid_search": True}  
    5| )  
    6|   
    7| # Adjusting number of retrieved chunks  
    8| client.retrieval.rag(  
    9|     query="your question",  
    10|     vector_search_settings={"limit": 30}  
    11| )  
  
  2. **Generation Settings** :


    
    
    1| # Adjusting response style  
    ---|---  
    2| client.retrieval.rag(  
    3|     query="your question",  
    4|     rag_generation_config={  
    5|         "temperature": 0.7,  
    6|         "model": "openai/gpt-4"  
    7|     }  
    8| )  
  
## How RAG works in R2R

R2R’s RAG implementation uses a sophisticated process:

**Document Processing**

  * Documents are split into semantic chunks
  * Each chunk is embedded using AI models
  * Chunks are stored with metadata and relationships



**Retrieval Process**

  * Queries are processed using hybrid search
  * Both semantic similarity and keyword matching are considered
  * Results are ranked by relevance scores



**Response Generation**

  * Retrieved chunks are formatted as context
  * The LLM generates responses using this context
  * Citations and references can be included



**Advanced Features**

  * GraphRAG for relationship-aware responses
  * Multi-step RAG for complex queries
  * Agent-based RAG for interactive conversations



## Best Practices

  1. **Document Processing**

     * Use appropriate chunk sizes (256-1024 tokens)
     * Maintain document metadata
     * Consider document relationships
  2. **Query Optimization**

     * Use hybrid search for better retrieval
     * Adjust relevance thresholds
     * Monitor and analyze search performance
  3. **Response Generation**

     * Balance temperature for creativity vs accuracy
     * Use system prompts for consistent formatting
     * Implement error handling and fallbacks



For more detailed information, visit our [RAG Configuration Guide](/self-hosting/configuration/retrieval/rag) or try our [Quickstart](/documentation/quickstart).

Was this page helpful?

YesNo

[Previous](/introduction/what-is-r2r)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# What is R2R? | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  *     * [Introduction](/introduction)
    * [System](/introduction/system)
    * [What's New](/introduction/whats-new)
  * Guides

    * [What is R2R?](/introduction/what-is-r2r)
    * [More about RAG](/introduction/rag)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [What does R2R do?](/introduction/what-is-r2r#what-does-r2r-do)
  * [What can R2R do for my applications?](/introduction/what-is-r2r#what-can-r2r-do-for-my-applications)
  * [What can R2R do for my developers?](/introduction/what-is-r2r#what-can-r2r-do-for-my-developers)
  * [What can R2R do for my business?](/introduction/what-is-r2r#what-can-r2r-do-for-my-business)
  * [Getting Started](/introduction/what-is-r2r#getting-started)



[Guides](/introduction/what-is-r2r)

# What is R2R?

Copy page

**On this page**

  1. What does R2R do?
  2. What can R2R do for my applications?
  3. What can R2R do for my developers?
  4. What can R2R do for my business?
  5. Getting started



Companies like OpenAI, Anthropic, and Google have shown the incredible potential of AI for understanding and generating human language. But building reliable AI applications that can work with your organization’s specific knowledge and documents requires significant expertise and infrastructure. Your company isn’t an AI infrastructure company: **it doesn’t make sense for you to build a complete AI retrieval ([RAG](/introduction/rag)) system from scratch.**

R2R provides the infrastructure and tools to help you implement **efficient, scalable, and reliable AI-powered document understanding** in your applications.

## What does R2R do?

R2R consists of three main components: **document processing** , **AI-powered search and generation** , and **analytics**. The document processing and search capabilities make it easier for your developers to create intelligent applications that can understand and work with your organization’s knowledge. The analytics tools enable your teams to monitor performance, understand usage patterns, and continuously improve the system.

## What can R2R do for my applications?

R2R provides your applications with production-ready RAG capabilities:

  * Fast and accurate document search using both semantic and keyword matching
  * Intelligent document processing that works with PDFs, images, audio, and more
  * Automatic relationship extraction to build knowledge graphs
  * Built-in user management and access controls
  * Simple integration through REST APIs and SDKs



## What can R2R do for my developers?

R2R provides a complete toolkit that simplifies building AI-powered applications:

  * [**Ready-to-use Docker deployment**](/self-hosting/installation/overview) for quick setup and testing
  * [**Python and JavaScript SDKs**](/api-and-sdks/introduction) for easy integration
  * **RESTful API** for language-agnostic access
  * [**Flexible configuration**](/self-hosting/configuration/overview) through intuitive config files
  * **Comprehensive documentation** and examples
  * [**Local deployment option**](/self-hosting/local-rag) for working with sensitive data



## What can R2R do for my business?

R2R provides the infrastructure to build AI applications that can:

  * **Make your documents searchable** with state of the art AI
  * **Answer questions** using your organization’s knowledge
  * **Process and understand** documents at scale
  * **Secure sensitive information** through built-in access controls
  * **Monitor usage and performance** through analytics
  * **Scale efficiently** as your needs grow



## Getting Started

The fastest way to start with R2R is through Docker:
    
    
    1| pip install r2r  
    ---|---  
    2| r2r serve --docker  
  
This gives you a complete RAG system running at [http://localhost:7272](http://localhost:7272/) with:

  * Document ingestion and processing
  * Vector search capabilities
  * GraphRAG features
  * User management
  * Analytics dashboard



Visit our [Quickstart Guide](/documentation/quickstart) to begin building with R2R.

Was this page helpful?

YesNo

[Previous](/introduction/whats-new)#### [More about RAGNext](/introduction/rag)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Users | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * [Overview](/documentation/overview)
    * [Quickstart](/documentation/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * General

    * [Documents](/documentation/documents)
    * [Conversations](/documentation/conversations)
    * [Collections](/documentation/collections)
    * [Graphs](/documentation/graphs)
    * [Prompts](/documentation/prompts)
    * [Users](/documentation/user-auth)
  * Retrieval

    * [Search and RAG](/documentation/search-and-rag)
    * [Agentic RAG](/documentation/retrieval/agentic-rag)
    * [Hybrid Search](/documentation/hybrid-search)
    * [Advanced RAG](/documentation/advanced-rag)
  * Advanced

    * [Deduplication](/documentation/deduplication)
    * [Contextual Enrichment](/documentation/contextual-enrichment)
  * Other

    * SciPhi Cloud




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Core Concepts](/documentation/user-auth#core-concepts)
  * [Authentication](/documentation/user-auth#authentication)
  * [User Management](/documentation/user-auth#user-management)
  * [Profile Information](/documentation/user-auth#profile-information)
  * [Role-Based Access](/documentation/user-auth#role-based-access)
  * [API Access](/documentation/user-auth#api-access)
  * [Security Features](/documentation/user-auth#security-features)
  * [Account Protection](/documentation/user-auth#account-protection)
  * [Email Security](/documentation/user-auth#email-security)
  * [Document Management](/documentation/user-auth#document-management)
  * [Enterprise Features](/documentation/user-auth#enterprise-features)
  * [Conclusion](/documentation/user-auth#conclusion)



[General](/documentation/documents)

# Users

Copy page

Manage users and authentication

##### 

User management features are currently restricted to:

  * Self-hosted instances
  * Enterprise tier cloud accounts



Contact our sales team for Enterprise pricing and features.

R2R provides a comprehensive user management and authentication system that enables secure access control, user administration, and profile management. This system serves as the foundation for document ownership, collection permissions, and collaboration features throughout R2R.

Refer to the [users API and SDK reference](/api-and-sdks/users/users) for detailed examples for interacting with users.

## Core Concepts

R2R’s user system is built around three fundamental principles. First, it ensures secure authentication through multiple methods including email/password and API keys. Second, it provides flexible authorization with role-based access control. Third, it maintains detailed user profiles that integrate with R2R’s document and collection systems.

## Authentication

Users can authenticate with R2R through several secure methods. Traditional email and password authentication provides standard access, while API keys enable programmatic integration. The system supports session management with refresh tokens for extended access and automatic session expiration for security.

When email verification is enabled, new users must verify their email address before gaining full system access. This verification process helps prevent unauthorized accounts and ensures reliable communication channels for important system notifications.

## User Management

### Profile Information

Each user in R2R has a comprehensive profile that includes:

  1. Core Identity

     * Email address (unique identifier)
     * Display name
     * Optional biography and profile picture
  2. System Status

     * Account creation date
     * Active/inactive status
     * Verification status
     * Last activity timestamp



### Role-Based Access

R2R implements a straightforward but powerful role system:

Regular users can manage their own content, including:

  * Creating and managing documents
  * Participating in collections they’re granted access to
  * Managing their profile and authentication methods



Superusers have additional system-wide capabilities:

  * Managing other user accounts
  * Accessing system settings and configurations
  * Viewing usage analytics and audit logs
  * Overriding standard permission limits



## API Access

R2R provides flexible API access through dedicated API keys. Users can:

  * Generate multiple API keys for different applications
  * Name and track individual keys
  * Monitor key usage and last-access times
  * Rotate or revoke keys as needed



The system maintains a clear audit trail of API key creation, usage, and deletion to help users manage their programmatic access securely.

## Security Features

### Account Protection

R2R implements multiple security measures to protect user accounts:

  * Strong password requirements
  * Secure password reset flows
  * Session management and forced logout capabilities
  * Activity monitoring and suspicious behavior detection



### Email Security

The email system handles several security-critical functions:

  * Account verification for new users
  * Secure password reset workflows
  * Important security notifications
  * System alerts and updates



## Document Management

Users automatically become owners of documents they create, granting them full control over those resources. Through collections, users can:

  * Share documents with other users
  * Set document permissions
  * Track document usage and access
  * Manage document lifecycles



## Enterprise Features

##### 

The following features require an Enterprise license or self-hosted installation. Contact our sales team for details.

Enterprise deployments gain access to advanced user management features including:

  * Single Sign-On (SSO) integration
  * Advanced user analytics and reporting
  * Custom user fields and metadata
  * Bulk user management tools
  * Enhanced security policies and controls



## Conclusion

The R2R user system provides a secure and flexible foundation for document management and collaboration. Through careful design and robust security measures, it enables both simple user management and complex enterprise scenarios while maintaining strong security standards.

Was this page helpful?

YesNo

[Previous](/documentation/prompts)#### [Search and RAGNext](/documentation/search-and-rag)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Web Development | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Data Processing and Retrieval

    * [Ingestion](/cookbooks/ingestion)
    * [Knowledge Graphs](/cookbooks/graphs)
    * [User-Defined Agent Tools](/cookbooks/custom-tools)
  * System Operations

    * [Email Verification](/cookbooks/email)
    * [Maintenance & Scaling](/cookbooks/maintenance)
    * [Orchestration](/cookbooks/orchestration)
  * Other

    * [Local LLMs](/cookbooks/local-llms)
    * [Structured Output](/cookbooks/structured-output)
    * [MCP](/cookbooks/other/mcp)
    * [Web Development](/cookbooks/web-dev)
    * [Evals](/cookbooks/other/evals)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Hello R2R—JavaScript](/cookbooks/web-dev#hello-r2rjavascript)
  * [r2r-js Client](/cookbooks/web-dev#r2r-js-client)
  * [Installing](/cookbooks/web-dev#installing)
  * [Creating the Client](/cookbooks/web-dev#creating-the-client)
  * [Log into the server](/cookbooks/web-dev#log-into-the-server)
  * [Ingesting Files](/cookbooks/web-dev#ingesting-files)
  * [Performing RAG](/cookbooks/web-dev#performing-rag)
  * [Connecting to a Web App](/cookbooks/web-dev#connecting-to-a-web-app)
  * [Setting up an API Route](/cookbooks/web-dev#setting-up-an-api-route)
  * [Frontend: React Component](/cookbooks/web-dev#frontend-react-component)
  * [Template Repository](/cookbooks/web-dev#template-repository)



[Other](/cookbooks/local-llms)

# Web Development

Copy page

Learn how to build webapps powered by RAG using R2R

Web developers can easily integrate R2R into their projects using the [R2R JavaScript client](https://www.npmjs.com/package/r2r-js). For more extensive reference and examples of how to use the r2r-js library, we encourage you to look at the [R2R Application](https://github.com/SciPhi-AI/R2R-Application) and its source code.

## Hello R2R—JavaScript

R2R gives developers configurable vector search and RAG right out of the box, as well as direct method calls instead of the client-server architecture seen throughout the docs:

r2r-js/examples/hello_r2r.js
    
    
    1| const { r2rClient } = require("r2r-js");  
    ---|---  
    2|   
    3| const client = new r2rClient("http://localhost:7272");  
    4|   
    5| async function main() {  
    6|   const files = [  
    7|     { path: "examples/data/raskolnikov.txt", name: "raskolnikov.txt" },  
    8|   ];  
    9|   
    10|   const EMAIL = "admin@example.com";  
    11|   const PASSWORD = "change_me_immediately";  
    12|   console.log("Logging in...");  
    13|   await client.users.login(EMAIL, PASSWORD);  
    14|   
    15|   console.log("Ingesting file...");  
    16|   const documentResult = await client.documents.create({  
    17|       file: { path: "examples/data/raskolnikov.txt", name: "raskolnikov.txt" },  
    18|       metadata: { title: "raskolnikov.txt" },  
    19|   });  
    20|   
    21|   console.log("Document result:", JSON.stringify(documentResult, null, 2));  
    22|   
    23|   console.log("Performing RAG...");  
    24|   const ragResponse = await client.rag({  
    25|     query: "What does the file talk about?",  
    26|     rag_generation_config: {  
    27|       model: "openai/gpt-4o",  
    28|       temperature: 0.0,  
    29|       stream: false,  
    30|     },  
    31|   });  
    32|   
    33|   console.log("Search Results:");  
    34|   ragResponse.results.search_results.chunk_search_results.forEach(  
    35|     (result, index) => {  
    36|       console.log(`\nResult ${index + 1}:`);  
    37|       console.log(`Text: ${result.metadata.text.substring(0, 100)}...`);  
    38|       console.log(`Score: ${result.score}`);  
    39|     },  
    40|   );  
    41|   
    42|   console.log("\nCompletion:");  
    43|   console.log(ragResponse.results.completion.choices[0].message.content);  
    44| }  
    45|   
    46| main();  
  
## r2r-js Client

### Installing

To get started, install the R2R JavaScript client with [npm](https://www.npmjs.com/package/r2r-js):

###### npm
    
    
    1| npm install r2r-js  
    ---|---  
  
### Creating the Client

First, we create the R2R client and specify the base URL where the R2R server is running:
    
    
    1| const { r2rClient } = require("r2r-js");  
    ---|---  
    2|   
    3| // http://localhost:7272 or the address that you are running the R2R server  
    4| const client = new r2rClient("http://localhost:7272");  
  
### Log into the server

Sign into the server to authenticate the session. We’ll use the default superuser credentials:
    
    
    1| const EMAIL = "admin@example.com";  
    ---|---  
    2| const PASSWORD = "change_me_immediately";  
    3| console.log("Logging in...");  
    4| await client.users.login(EMAIL, PASSWORD);  
  
### Ingesting Files

Specify the files that we’ll ingest:
    
    
    1| const file = { path: "examples/data/raskolnikov.txt", name: "raskolnikov.txt" }  
    ---|---  
    2| ];  
    3| console.log("Ingesting file...");  
    4| const ingestResult = await client.documents.create(  
    5|   file: { path: "examples/data/raskolnikov.txt", name: "raskolnikov.txt" },  
    6|   metadata: { title: "raskolnikov.txt" },  
    7| )  
    8| console.log("Ingest result:", JSON.stringify(ingestResult, null, 2));  
    9| ...  
    10| /* Ingest result: {  
    11|   "results": {  
    12|     "processed_documents": [  
    13|       "Document 'raskolnikov.txt' processed successfully."  
    14|     ],  
    15|     "failed_documents": [],  
    16|     "skipped_documents": []  
    17|   }  
    18| } */  
  
This command processes the ingested, splits them into chunks, embeds the chunks, and stores them into your specified Postgres database. Relational data is also stored to allow for downstream document management, which you can read about in the [quickstart](/documentation/quickstart).

### Performing RAG

We’ll make a RAG request,
    
    
    1| console.log("Performing RAG...");  
    ---|---  
    2|   const ragResponse = await client.rag({  
    3|     query: "What does the file talk about?",  
    4|     rag_generation_config: {  
    5|       model: "openai/gpt-4o",  
    6|       temperature: 0.0,  
    7|       stream: false,  
    8|     },  
    9|   });  
    10|   
    11| console.log("Search Results:");  
    12|   ragResponse.results.search_results.chunk_search_results.forEach(  
    13|     (result, index) => {  
    14|       console.log(`\nResult ${index + 1}:`);  
    15|       console.log(`Text: ${result.metadata.text.substring(0, 100)}...`);  
    16|       console.log(`Score: ${result.score}`);  
    17|     },  
    18|   );  
    19|   
    20|   console.log("\nCompletion:");  
    21|   console.log(ragResponse.results.completion.choices[0].message.content);  
    22| ...  
    23| /* Performing RAG...  
    24| Search Results:  
    25|   
    26| Result 1:  
    27| Text: praeterire culinam eius, cuius ianua semper aperta erat, cogebatur. Et quoties praeteribat,  
    28| iuvenis ...  
    29| Score: 0.08281802143835804  
    30|   
    31| Result 2:  
    32| Text: In vespera praecipue calida ineunte Iulio iuvenis e cenaculo in quo hospitabatur in  
    33| S. loco exiit et...  
    34| Score: 0.052743945852283036  
    35|   
    36| Completion:  
    37| The file discusses the experiences and emotions of a young man who is staying in a small room in a tall house.  
    38| He is burdened by debt and feels anxious and ashamed whenever he passes by the kitchen of his landlady, whose  
    39| door is always open [1]. On a particularly warm evening in early July, he leaves his room and walks slowly towards  
    40| a bridge, trying to avoid encountering his landlady on the stairs. His room, which is more like a closet than a  
    41| proper room, is located under the roof of the five-story house, while the landlady lives on the floor below and  
    42| provides him with meals and services [2].  
    43| */  
  
## Connecting to a Web App

R2R can be easily integrated into web applications. We’ll create a simple Next.js app that uses R2R for query answering. [We’ve created a template repository with this code.](https://github.com/SciPhi-AI/r2r-webdev-template)

Alternatively, you can add the code below to your own Next.js project.

![R2R Dashboard Overview](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/R2R_Web_Dev_Template.png)

### Setting up an API Route

First, we’ll create an API route to handle R2R queries. Create a file named `r2r-query.ts` in the `pages/api` directory:

###### r2r-query.ts
    
    
    1| import { NextApiRequest, NextApiResponse } from 'next';  
    ---|---  
    2| import { r2rClient } from 'r2r-js';  
    3|   
    4| const client = new r2rClient("http://localhost:7272");  
    5|   
    6| export default async function handler(req: NextApiRequest, res: NextApiResponse) {  
    7|   if (req.method === 'POST') {  
    8|     const { query } = req.body;  
    9|   
    10|     try {  
    11|       // Login with each request. In a production app, you'd want to manage sessions.  
    12|       await client.users.login("admin@example.com", "change_me_immediately");  
    13|   
    14|       const response = await client.rag({  
    15|         query: query,  
    16|         rag_generation_config: {  
    17|           model: "openai/gpt-4o",  
    18|           temperature: 0.0,  
    19|           stream: false,  
    20|         }  
    21|       });  
    22|   
    23|       res.status(200).json({ result: response.results.completion.choices[0].message.content });  
    24|     } catch (error) {  
    25|       res.status(500).json({ error: error instanceof Error ? error.message : 'An error occurred' });  
    26|     }  
    27|   } else {  
    28|     res.setHeader('Allow', ['POST']);  
    29|     res.status(405).end(`Method ${req.method} Not Allowed`);  
    30|   }  
    31| }  
  
This API route creates an R2R client, logs in, and processes the incoming query using the RAG method.

### Frontend: React Component

Next, create a React component to interact with the API. Here’s an example `index.tsx` file:

###### index.tsx
    
    
    1| import React, { useState } from 'react';  
    ---|---  
    2| import styles from '@/styles/R2RWebDevTemplate.module.css';  
    3|   
    4| const R2RQueryApp: React.FC = () => {  
    5|   const [query, setQuery] = useState('');  
    6|   const [result, setResult] = useState('');  
    7|   const [isLoading, setIsLoading] = useState(false);  
    8|   
    9|   const performQuery = async () => {  
    10|     setIsLoading(true);  
    11|     setResult('');  
    12|   
    13|     try {  
    14|       const response = await fetch('/api/r2r-query', {  
    15|         method: 'POST',  
    16|         headers: {  
    17|           'Content-Type': 'application/json',  
    18|         },  
    19|         body: JSON.stringify({ query }),  
    20|       });  
    21|   
    22|       if (!response.ok) {  
    23|         throw new Error('Network response was not ok');  
    24|       }  
    25|   
    26|       const data = await response.json();  
    27|       setResult(data.result);  
    28|     } catch (error) {  
    29|       setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);  
    30|     } finally {  
    31|       setIsLoading(false);  
    32|     }  
    33|   };  
    34|   
    35|   return (  
    36|     <div className={styles.appWrapper}>  
    37|       <h1 className={styles.title}>R2R Web Dev Template</h1>  
    38|       <p>A simple template for making RAG queries with R2R.  
    39|         Make sure that your R2R server is up and running, and that you've ingested files!  
    40|       </p>  
    41|       <p>  
    42|         Check out the <a href="https://r2r-docs.sciphi.ai/" target="_blank" rel="noopener noreferrer">R2R Documentation</a> for more information.  
    43|       </p>  
    44|       <input  
    45|         type="text"  
    46|         value={query}  
    47|         onChange={(e) => setQuery(e.target.value)}  
    48|         placeholder="Enter your query here"  
    49|         className={styles.queryInput}  
    50|       />  
    51|       <button  
    52|         onClick={performQuery}  
    53|         disabled={isLoading}  
    54|         className={styles.submitButton}  
    55|       >  
    56|         Submit Query  
    57|       </button>  
    58|       {isLoading ? (  
    59|         <div className={styles.spinner} />  
    60|       ) : (  
    61|         <div className={styles.resultDisplay}>{result}</div>  
    62|       )}  
    63|     </div>  
    64|   );  
    65| };  
    66|   
    67| export default R2RQueryApp;  
  
This component creates a simple interface with an input field for the query and a button to submit it. When the button is clicked, it sends a request to the API route we created earlier and displays the result.

### Template Repository

For a complete working example, you can check out our template repository. This repository contains a simple Next.js app with R2R integration, providing a starting point for your own R2R-powered web applications.

For more advanced examples, check out the [source code for the R2R Dashboard.](https://github.com/SciPhi-AI/R2R-Application)

[R2R Web App Template Repository](https://github.com/SciPhi-AI/r2r-webdev-template)

To use this template:

  1. Clone the repository
  2. Install dependencies with `pnpm install`
  3. Make sure your R2R server is running
  4. Start the development server with `pnpm dev`



This template provides a foundation for building more complex applications with R2R, demonstrating how to integrate R2R’s powerful RAG capabilities into a web interface.

Was this page helpful?

YesNo

[Previous](/cookbooks/other/mcp)#### [EvalsNext](/cookbooks/other/evals)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Data Ingestion | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * Installation

    * [Quickstart](/self-hosting/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * Configuration Files

    * [Overview](/self-hosting/configuration/overview)
    * [Database](/self-hosting/configuration/database)
    * [File Storage](/self-hosting/configuration/file-storage)
    * [Embedding](/self-hosting/configuration/embedding)
    * [LLMs](/self-hosting/configuration/llm)
    * [Email](/self-hosting/configuration/email)
    * [Crypto](/self-hosting/configuration/crypto)
    * [Auth](/self-hosting/configuration/auth)
    * [Scheduler](/self-hosting/configuration/scheduler)
    * [Orchestration](/self-hosting/configuration/orchestration)
    * [Agent](/self-hosting/configuration/agent)
    * [Ingestion](/self-hosting/configuration/ingestion)
  * Retrieval and generation

    * [Overview](/self-hosting/configuration/retrieval/overview)
    * [RAG](/self-hosting/configuration/retrieval/rag)
    * [Graphs](/self-hosting/configuration/knowledge-graph/overview)
    * [Prompts](/self-hosting/configuration/retrieval/prompts)
  * System

    * [Local LLMs](/self-hosting/local-rag)
  * Deployment

    * [Introduction](/self-hosting/deployment/introduction)
    * Cloud Providers

  * Users

    * [User Auth](/self-hosting/user-auth)
    * [Collections](/self-hosting/collections)
    * [Application](/self-hosting/application)
  * Other

    * Telemetry




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Introduction](/self-hosting/configuration/ingestion#introduction)
  * [Supported File Types](/self-hosting/configuration/ingestion#supported-file-types)
  * [Deployment Options](/self-hosting/configuration/ingestion#deployment-options)
  * [Ingestion Modes](/self-hosting/configuration/ingestion#ingestion-modes)
  * [Core Concepts](/self-hosting/configuration/ingestion#core-concepts)
  * [Document Processing](/self-hosting/configuration/ingestion#document-processing)
  * [Ingestion Architecture](/self-hosting/configuration/ingestion#ingestion-architecture)
  * [Multimodal Support](/self-hosting/configuration/ingestion#multimodal-support)
  * [Configuration](/self-hosting/configuration/ingestion#configuration)
  * [Key Configuration Areas](/self-hosting/configuration/ingestion#key-configuration-areas)
  * [Configuration Impact](/self-hosting/configuration/ingestion#configuration-impact)
  * [Document Management](/self-hosting/configuration/ingestion#document-management)
  * [Document Ingestion](/self-hosting/configuration/ingestion#document-ingestion)
  * [Next Steps](/self-hosting/configuration/ingestion#next-steps)



[Configuration Files](/self-hosting/configuration/overview)

# Data Ingestion

Copy page

Configuring ingestion

## Introduction

R2R’s ingestion workflows transforms raw documents into structured, searchable content. It supports a wide range of file types and can run in different modes and configurations to suit your performance and quality requirements.

Data ingestion seamlessly integrates with R2R’s vector databases and knowledge graphs, enabling advanced retrieval, analysis, and entity/relationship extraction at scale.

### Supported File Types

R2R supports ingestion of the following document types:

Category| File types  
---|---  
Image| `.bmp`, `.heic`, `.jpeg`, `.png`, `.tiff`  
MP3| `.mp3`  
PDF| `.pdf`  
CSV| `.csv`  
E-mail| `.eml`, `.msg`, `.p7s`  
EPUB| `.epub`  
Excel| `.xls`, `.xlsx`  
HTML| `.html`  
Markdown| `.md`  
Org Mode| `.org`  
Open Office| `.odt`  
Plain text| `.txt`  
PowerPoint| `.ppt`, `.pptx`  
reStructured Text| `.rst`  
Rich Text| `.rtf`  
TSV| `.tsv`  
Word| `.doc`, `.docx`  
Code| `.py`, `.js`, `.ts`, `.css`  
  
### Deployment Options

R2R ingestion works in two main deployment modes:

  * **Light** :  
Uses R2R’s built-in parsing for synchronous ingestion. This mode is simple, fast, and supports all file types locally. It’s ideal for lower-volume scenarios or quick testing.

  * **Full** :  
Employs workflow orchestration to run asynchronous ingestion tasks at higher throughput. It can leverage external providers like `unstructured_local` or `unstructured_api` for more advanced parsing capabilities and hybrid (text + image) analysis.




### Ingestion Modes

When creating or updating documents, you can select an ingestion mode based on your needs:

  * **`fast`** : Prioritizes speed by skipping certain enrichment steps like summarization.
  * **`hi-res`** : Aims for high-quality extraction, potentially leveraging visual language models for PDFs and images. Recommended for complex or multimodal documents.
  * **`custom`** : Offers full control via `ingestion_config`, allowing you to tailor parsing, chunking, and enrichment parameters.



## Core Concepts

### Document Processing

Ingestion in R2R covers the entire lifecycle of a document’s preparation for retrieval:

  1. **Parsing** : Converts source files into text.
  2. **Chunking** : Breaks text into semantic segments.
  3. **Embedding** : Transforms segments into vector representations for semantic search.
  4. **Storing** : Persists chunks and embeddings for retrieval.
  5. **Knowledge Graph Integration** : Optionally extracts entities and relationships for graph-based analysis.



Each ingested document is associated with user permissions and metadata, enabling comprehensive access control and management.

## Ingestion Architecture

R2R’s ingestion is modular and extensible:

This structure allows you to customize components (e.g., choose a different parser or embedding model) without disrupting the entire system.

### Multimodal Support

For documents that contain images, complex layouts, or mixed media (like PDFs), using `hi-res` mode can unlock visual language model (VLM) capabilities. On a **full** deployment, `hi-res` mode may incorporate `unstructured_local` or `unstructured_api` to handle these advanced parsing scenarios.

## Configuration

### Key Configuration Areas

Ingestion behavior is primarily managed through your `r2r.toml` configuration file:
    
    
    1| [ingestion]  
    ---|---  
    2| provider = "r2r" # or `unstructured_local` | `unstructured_api`  
    3| chunking_strategy = "recursive"  
    4| chunk_size = 1024  
    5| chunk_overlap = 512  
  
  * **Provider** : Determines which parsing engine is used (`r2r` built-in or `unstructured_*` providers).
  * **Chunking Strategy & Parameters**: Control how text is segmented into chunks.
  * **Other Settings** : Adjust file parsing logic, excluded parsers, and integration with embeddings or knowledge graphs.



### Configuration Impact

Your ingestion settings influence:

  1. **[Postgres Configuration](/self-hosting/configuration/database)** :  
Ensures that vector and metadata storage are optimized for semantic retrieval.

  2. **[Embedding Configuration](/self-hosting/configuration/embedding)** :  
Defines the vector models and parameters used to embed document chunks and queries.

  3. **Ingestion Settings Themselves** :  
Affect parsing complexity, chunk sizes, and the extent of enrichment during ingestion.




## Document Management

### Document Ingestion

R2R supports multiple ingestion methods:

  * **File Ingestion** : Provide a file path and optional metadata:
        
        1| ingest_response = client.documents.create(  
        ---|---  
        2|     file_path="path/to/file.txt",  
        3|     metadata={"key1": "value1"},  
        4|     ingestion_mode="fast", # choose fast, hi-res, or custom  
        5|     # ingestion_config = {...} # `custom` setting allows for full specification  
        6| )  
  
  * **Direct Chunk Ingestion** : Supply pre-processed text segments:
        
        1| chunks = ["Pre-chunked content", "other pre-chunked content", ...]  
        ---|---  
        2| ingest_response = client.documents.create(chunks=chunks)  
  



## Next Steps

  * Review [Embedding Configuration](/self-hosting/configuration/embedding) to optimize semantic search.
  * Check out other configuration guides for integrating retrieval and knowledge graph capabilities.



Was this page helpful?

YesNo

[Previous](/self-hosting/configuration/agent)#### [Retrieval ConfigurationConfigure your retrieval systemNext](/self-hosting/configuration/retrieval/overview)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Introduction | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  *     * [Introduction](/introduction)
    * [System](/introduction/system)
    * [What's New](/introduction/whats-new)
  * Guides

    * [What is R2R?](/introduction/what-is-r2r)
    * [More about RAG](/introduction/rag)



[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Cloud Documentation](/introduction#cloud-documentation)
  * [Getting Started](/introduction#getting-started)
  * [Key Features](/introduction#key-features)
  * [Ingestion & Retrieval](/introduction#ingestion--retrieval)
  * [Application Layer](/introduction#application-layer)
  * [Self-Hosting](/introduction#self-hosting)
  * [Community](/introduction#community)
  * [About](/introduction#about)



# Introduction

Copy page

The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

![r2r](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/images/r2r.png)

R2R is an all-in-one solution for AI Retrieval-Augmented Generation (RAG) with production-ready features, including multimodal content ingestion, hybrid search functionality, configurable GraphRAG, and user/document management.

R2R also includes a **Deep Research API** , a multi-step reasoning system that fetches relevant data from your knowledgebase and/or the internet to deliver richer, context-aware answers for complex queries.

* * *

# Cloud Documentation

## Getting Started

  * 🚀 **[Quickstart](/documentation/quickstart)** A quick introduction to R2R’s core features.
  * ❇️ **[API& SDKs](/api-and-sdks/introduction)** API reference and Python/JS SDKs for interacting with R2R.



## Key Features

### Ingestion & Retrieval

  * **📁[Multimodal Ingestion](/self-hosting/configuration/ingestion)** Parse `.txt`, `.pdf`, `.json`, `.png`, `.mp3`, and more.
  * **🔍[Hybrid Search](/documentation/search-and-rag)** Combine semantic and keyword search with reciprocal rank fusion for enhanced relevancy.
  * **🔗[Knowledge Graphs](/cookbooks/graphs)** Automatically extract entities and relationships to build knowledge graphs.
  * **🤖[Agentic RAG](/documentation/retrieval/agentic-rag)** R2R’s powerful Deep Research agent integrated with RAG over your knowledgebase.



### Application Layer

  * 💻 **[Web Development](/cookbooks/web-dev)** Building web apps using R2R.
  * 🔐 **[User Auth](/documentation/user-auth)** Authenticating users.
  * 📂 **[Collections](/self-hosting/collections)** Document collections management.
  * 🌐 **[Web Application](/cookbooks/web-dev)** Connecting with the R2R Application.



### Self-Hosting

  * 🐋 **[Docker](/self-hosting/installation/full)** Use Docker to easily deploy the full R2R system into your local environment
  * 🧩 **[Configuration](/self-hosting/configuration/overview)** Set up your application using intuitive configuration files.



* * *

# Community

[Join our Discord server](https://discord.gg/p6KqD2kjtB) to get support and connect with both the R2R team and other developers. Whether you’re encountering issues, seeking best practices, or sharing your experiences, we’re here to help.

* * *

# About

  * **🌐[SciPhi Website](https://sciphi.ai/)** Explore a managed AI solution powered by R2R.
  * **✉️[Contact Us](mailto:///founders@sciphi.ai)** Get in touch with our team to discuss your specific needs.



Was this page helpful?

YesNo

#### [SystemLearn about the R2R system architectureNext](/introduction/system)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# R2R Full Installation | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * Installation

    * [Quickstart](/self-hosting/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * Configuration Files

    * [Overview](/self-hosting/configuration/overview)
    * [Database](/self-hosting/configuration/database)
    * [File Storage](/self-hosting/configuration/file-storage)
    * [Embedding](/self-hosting/configuration/embedding)
    * [LLMs](/self-hosting/configuration/llm)
    * [Email](/self-hosting/configuration/email)
    * [Crypto](/self-hosting/configuration/crypto)
    * [Auth](/self-hosting/configuration/auth)
    * [Scheduler](/self-hosting/configuration/scheduler)
    * [Orchestration](/self-hosting/configuration/orchestration)
    * [Agent](/self-hosting/configuration/agent)
    * [Ingestion](/self-hosting/configuration/ingestion)
  * Retrieval and generation

    * [Overview](/self-hosting/configuration/retrieval/overview)
    * [RAG](/self-hosting/configuration/retrieval/rag)
    * [Graphs](/self-hosting/configuration/knowledge-graph/overview)
    * [Prompts](/self-hosting/configuration/retrieval/prompts)
  * System

    * [Local LLMs](/self-hosting/local-rag)
  * Deployment

    * [Introduction](/self-hosting/deployment/introduction)
    * Cloud Providers

  * Users

    * [User Auth](/self-hosting/user-auth)
    * [Collections](/self-hosting/collections)
    * [Application](/self-hosting/application)
  * Other

    * Telemetry




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Prerequisites](/self-hosting/installation/full#prerequisites)
  * [Installation](/self-hosting/installation/full#installation)
  * [Next Steps](/self-hosting/installation/full#next-steps)



[Getting Started](/self-hosting/installation/overview)[Installation](/self-hosting/installation/overview)

# R2R Full Installation

Copy page

##### 

This installation guide is for Full R2R. For solo developers or teams prototyping, we recommend starting with [R2R Light](/self-hosting/installation/light).

This guide will walk you through installing and running R2R using Docker, which is the quickest and easiest way to get started.

## Prerequisites

  * Docker installed on your system. If you haven’t installed Docker yet, please refer to the [official Docker installation guide](https://docs.docker.com/engine/install/).



## Installation

[1](/self-hosting/installation/full#clone-the-r2r-repository)

### Clone the R2R repository

Clone the R2R repository for access to the Docker compose files:
    
    
    1| git clone https://github.com/SciPhi-AI/R2R.git  
    ---|---  
    2| cd R2R/docker  
  
[2](/self-hosting/installation/full#set-environment-variables)

### Set environment variables

##### 

The full R2R installation uses a pre-built custom configuration [`full.toml`](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/full.toml) rather than the default [`r2r.toml`](https://github.com/SciPhi-AI/R2R/blob/main/py/r2r/r2r.toml).

Navigate to the env directory and set up your environment variables:
    
    
    1| cd env  
    ---|---  
    2| # Edit r2r-full.env with your preferred text editor  
    3| sudo nano r2r-full.env  
  
### Required Environment Variables

### Configuration Selection (choose one)

Variable| Description| Default  
---|---|---  
`R2R_CONFIG_NAME`| Uses a predefined configuration| `full` (OpenAI)  
`R2R_CONFIG_PATH`| Path to your custom TOML config| None  
  
> Set `R2R_CONFIG_NAME=full_ollama` to use local models instead of cloud providers.

### LLM API Keys (at least one required)

Provider| Environment Variable| Used With  
---|---|---  
OpenAI| `OPENAI_API_KEY`| `R2R_CONFIG_NAME=full`  
Anthropic| `ANTHROPIC_API_KEY`| Custom config or runtime overrides  
Ollama| `OLLAMA_API_BASE`| `R2R_CONFIG_NAME=full_ollama`  
  
> For Ollama, the default value is `http://host.docker.internal:11434`

### External Agent Tools (optional)

Tool| Environment Variable| Purpose| Provider Link  
---|---|---|---  
`web_search`| `SERPER_API_KEY`| Enable web search tool| [Serper](https://serper.dev/)  
`web_scrape`| `FIRECRAWL_API_KEY`| Enable web scrape tool| [Firecrawl](https://www.firecrawl.dev/)  
  
##### 

These environment variables are only required if you plan to use the `web_search` or `web_scrape` tools with the Agentic RAG functionality. R2R will function without these for local document operations.

When starting R2R with agent tools, include these variables with your launch command:
    
    
    $| # Example with Cloud LLMs and Agent Tools  
    ---|---  
    >| export OPENAI_API_KEY=sk-...  
    >| export ANTHROPIC_API_KEY=sk-...  
    >| export SERPER_API_KEY=your_serper_api_key_here  
    >| export FIRECRAWL_API_KEY=your_firecrawl_api_key_here  
    >|   
    >| COMPOSE_PROFILES=postgres docker compose -f compose.full.yaml up -d  
  
[See the full configuration guide](/self-hosting/configuration/overview) for additional options.

[3](/self-hosting/installation/full#custom-configuration-optional)

### Custom Configuration (Optional)

If you’re using a custom configuration file instead of the built-in options, follow these steps:

  1. Create a TOML configuration file in the `user_configs` directory:


    
    
    1| # Navigate to the user_configs directory  
    ---|---  
    2| cd user_configs  
    3|   
    4| # Create a new configuration file (e.g., my_config.toml)  
    5| touch my_config.toml  
    6|   
    7| # Edit the file with your configuration settings  
    8| nano my_config.toml  
  
  2. Update your `r2r-full.env` file to point to this configuration:


    
    
    R2R_CONFIG_PATH=/app/user_configs/my_config.toml  
    ---  
  
##### 

The path in `R2R_CONFIG_PATH` must use the container path (`/app/user_configs/`), not your local system path.

Make sure the specified configuration file actually exists in the `user_configs` directory. The application will fail to start if it cannot find the file at the specified path.

For examples and configuration templates, see the [Configuration Guide](/self-hosting/configuration/overview).

[4](/self-hosting/installation/full#start-the-r2r-services)

### Start the R2R services

Return to the docker directory and start the services:
    
    
    1| cd ..  
    ---|---  
    2| docker compose -f compose.full.yaml --profile postgres up -d  
    3| # `--profile postgres` can be omitted when using external Postgres  
  
[5](/self-hosting/installation/full#interact-with-r2r)

### Interact with R2R

Ether install the Python or JS SDK, or navigate to [http://localhost:7273](http://localhost:7273/) to interact with R2R via the dashboard.

To install the Python SDK:
    
    
    1| pip install r2r  
    ---|---  
  
## Next Steps

After successfully installing R2R:

  1. **Verify Installation** : Ensure all components are running correctly by accessing the R2R API at <http://localhost:7272/v3/health>[](http://localhost:7272/v3/health).

  2. **Quick Start** : Follow our [R2R Quickstart Guide](/self-hosting/quickstart) to set up your first RAG application.

  3. **In-Depth Tutorial** : For a more comprehensive understanding, work through our [R2R Walkthrough](/documentation/walkthrough).

  4. **Customize Your Setup** : [Configuration](/self-hosting/configuration/overview) your R2R system.




If you encounter any issues during installation or setup, please use our [Discord community](https://discord.gg/p6KqD2kjtB) or [GitHub repository](https://github.com/SciPhi-AI/R2R) to seek assistance.

Was this page helpful?

YesNo

[Previous](/self-hosting/installation/light)#### [QuickstartNext](/self-hosting/quickstart)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

# Overview | The most advanced AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API.

[![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_white.svg)![Logo](https://files.buildwithfern.com/https://sciphi.docs.buildwithfern.com/2025-05-20T17:18:43.700Z/logo/sciphi_black.svg)](/)

Search`/`[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

[Introduction](/introduction)[Documentation](/documentation/overview)[API & SDKs](/api-and-sdks/introduction)[Cookbooks](/cookbooks/ingestion)[Self Hosting](/self-hosting/installation/overview)

  * Getting Started

    * Installation

    * [Quickstart](/self-hosting/quickstart)
    * [Walkthrough](/documentation/walkthrough)
  * Configuration Files

    * [Overview](/self-hosting/configuration/overview)
    * [Database](/self-hosting/configuration/database)
    * [File Storage](/self-hosting/configuration/file-storage)
    * [Embedding](/self-hosting/configuration/embedding)
    * [LLMs](/self-hosting/configuration/llm)
    * [Email](/self-hosting/configuration/email)
    * [Crypto](/self-hosting/configuration/crypto)
    * [Auth](/self-hosting/configuration/auth)
    * [Scheduler](/self-hosting/configuration/scheduler)
    * [Orchestration](/self-hosting/configuration/orchestration)
    * [Agent](/self-hosting/configuration/agent)
    * [Ingestion](/self-hosting/configuration/ingestion)
  * Retrieval and generation

    * [Overview](/self-hosting/configuration/retrieval/overview)
    * [RAG](/self-hosting/configuration/retrieval/rag)
    * [Graphs](/self-hosting/configuration/knowledge-graph/overview)
    * [Prompts](/self-hosting/configuration/retrieval/prompts)
  * System

    * [Local LLMs](/self-hosting/local-rag)
  * Deployment

    * [Introduction](/self-hosting/deployment/introduction)
    * Cloud Providers

  * Users

    * [User Auth](/self-hosting/user-auth)
    * [Collections](/self-hosting/collections)
    * [Application](/self-hosting/application)
  * Other

    * Telemetry




[Community](https://discord.gg/p6KqD2kjtB)[Support](mailto:///founders@sciphi.ai)[R2R GitHub](https://github.com/SciPhi-AI/R2R)

Light

On this page

  * [Server-side Configuration](/self-hosting/configuration/overview#server-side-configuration)
  * [Custom Configuration Files](/self-hosting/configuration/overview#custom-configuration-files)
  * [Runtime Settings](/self-hosting/configuration/overview#runtime-settings)



[Configuration Files](/self-hosting/configuration/overview)

# Overview

Copy page

Configure your R2R deployment

R2R was built with configuration in mind and utilizes [TOML](https://toml.io/) configuration files to define server-side variables.

The levels of configuration that are supported are:

  1. **Server-side Configuration** : Define default configuration for your R2R deployment.
  2. **Runtime Settings** : Dynamically override configuration settings when making API calls.



## Server-side Configuration

R2R’s configuration format works by override. Default configuration values are defined in the [`r2r.toml`](https://github.com/SciPhi-AI/R2R/blob/main/py/r2r/r2r.toml) file.

A number of pre-defined configuration files ship with R2R, detailed below. For a complete list of configurable parameters and their defaults, refer to our [`all_possible_config.toml`](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/all_possible_config.toml) file.

##### 

Editing pre-defined configurations while running R2R with Docker will not have an effect; refer to the [installation guide](/self-hosting/installation/full) for instructions on how to use custom configs with Docker.

Configuration File| Usage  
---|---  
[r2r.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/r2r/r2r.toml)| The default R2R configuration file.  
[full.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/full.toml)| Includes orchestration with Hatchet.  
[full_azure.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/full_azure.toml)| Includes orchestration with Hatchet and Azure OpenAI models.  
[full_lm_studio.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/full_lm_studio.toml)| Includes orchestration with Hatchet and LM Studio models.  
[full_ollama.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/full_ollama.toml)| Includes orchestration with Hatchet and Ollama models.  
[r2r_azure.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/r2r_azure.toml)| Configured to run Azure OpenAI models.  
[gemini.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/gemini.toml)| Configured to run Gemini models.  
[lm_studio.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/lm_studio.toml)| Configured to run LM Studio models.  
[ollama.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/ollama.toml)| Configured to run Ollama models.  
[r2r_with_auth.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/r2r_with_auth.toml)| Configured to require user verification.  
[tavily.toml](https://github.com/SciPhi-AI/R2R/blob/main/py/core/configs/tavily.toml)| Configured to use the Tavily tool.  
  
### Custom Configuration Files

To create your own custom configuration:

  1. Create a new file named `my_r2r.toml` in your project directory.
  2. Add only the settings you wish to customize. For example:



my_r2r.toml
    
    
    1| [app]  
    ---|---  
    2| # LLM used for user-facing responses (high-quality outputs)  
    3| quality_llm = "openai/gpt-4o"  
    4| # LLM used for internal summarizations and similar tasks (fast responses)  
    5| fast_llm = "openai/gpt-4o-mini"  
    6|   
    7| [completion]  
    8|   [completion.generation_config]  
    9|   temperature = 0.7  
    10|   top_p = 0.9  
    11|   max_tokens_to_sample = 1024  
    12|   stream = false  
    13|   add_generation_kwargs = {}  
  
  3. Launch the R2R server with your custom configuration:


    
    
    1| export R2R_CONFIG_PATH=path_to_your_config  
    ---|---  
    2| python -m r2r.serve  
  
R2R will use your specified settings, falling back to the defaults defined in the main configuration files for any unspecified options.

## Runtime Settings

When calling endpoints, such as `retrieval/search` or `retrieval/rag`, you can override server-side configurations on-the-fly. This allows for dynamic control over search settings, model selection, prompt customization, and more.

For example, using the Python SDK:
    
    
    1| client = R2RClient("http://localhost:7272")  
    ---|---  
    2|   
    3| response = client.retrieval.rag(  
    4|     "Who was Aristotle?",  
    5|     rag_generation_config={  
    6|         "model": "anthropic/claude-3-haiku-20240307",  # Overrides the default quality_llm  
    7|         "temperature": 0.7  
    8|     },  
    9|     search_settings={  
    10|         "limit": 100,           # Number of search results to return  
    11|         "use_hybrid_search": True  # Enable semantic + full-text search  
    12|     }  
    13| )  
  
[Refer here](/self-hosting/configuration/retrieval/overview) to learn more about configuring and dynamically setting your retrieval system.

Was this page helpful?

YesNo

[Previous](/self-hosting/quickstart)#### [DatabaseConfiguring your DatabaseNext](/self-hosting/configuration/database)[Built with](https://buildwithfern.com/?utm_campaign=buildWith&utm_medium=docs&utm_source=r2r-docs.sciphi.ai)


---

