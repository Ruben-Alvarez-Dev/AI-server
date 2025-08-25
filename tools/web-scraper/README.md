# Memory-Server Web Scraper

Advanced web scraping tool integrated with Memory-Server for intelligent content extraction and processing.

## Features

- 🌐 **Playwright Integration**: Modern browser automation for JavaScript-heavy sites
- 🧹 **Content Cleaning**: Advanced text extraction and cleanup
- 📊 **Batch Processing**: Handle multiple URLs efficiently
- 🏷️ **Auto-Tagging**: Intelligent content categorization
- 🔄 **Memory-Server Integration**: Direct ingestion into workspaces
- ⚡ **Rate Limiting**: Respectful scraping with configurable delays

## Installation

```bash
# Install Python dependencies
pip install playwright beautifulsoup4 html2text aiohttp

# Install browser binaries
playwright install
```

## Configuration

The web scraper integrates with Memory-Server's existing `WebScraperService` and `WebSearchService` classes:

- **Location**: `api/utils/web_scraper.py`
- **Search Integration**: `api/utils/web_search.py`
- **API Endpoints**: `api/routers/web_search.py`

## Usage Examples

### Via API Endpoints

```bash
# Basic web scraping
curl -X POST "http://localhost:8001/api/v1/documents/scrape-web" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "workspace": "research",
    "max_pages": 5
  }'

# Search and scrape
curl -X POST "http://localhost:8001/api/v1/search/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python async programming",
    "num_results": 3,
    "workspace": "code",
    "auto_ingest": true
  }'
```

### Programmatic Usage

```python
from api.utils.web_scraper import WebScraperService

scraper = WebScraperService()

# Scrape single page
result = await scraper.scrape_url(
    url="https://example.com",
    workspace="research"
)

# Batch scraping
urls = ["https://site1.com", "https://site2.com"]
results = await scraper.batch_scrape_urls(
    urls=urls,
    workspace="research",
    max_concurrent=3
)
```

## Integration Points

### Memory-Server Workspaces
- Scraped content automatically categorized by workspace
- Intelligent auto-tagging based on content analysis
- Integration with ContentAnalyzer for enhanced metadata

### Search Integration
- Serper API for web search
- Firecrawl API for enhanced content extraction
- Automatic fallback to Playwright scraping

### API Endpoints
- `/api/v1/documents/scrape-web` - Single URL scraping
- `/api/v1/search/scrape` - Search and scrape workflow
- `/api/v1/search/documentation` - Documentation-focused scraping
- `/api/v1/search/forums` - Forum and community content

## Configuration Options

Web scraper behavior can be configured via Memory-Server settings:

```python
# In core/config.py
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max content size
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
```

## Best Practices

1. **Respectful Scraping**: Built-in delays and rate limiting
2. **Error Handling**: Robust retry mechanisms and fallbacks
3. **Content Quality**: Advanced cleaning and deduplication
4. **Privacy Compliance**: Respects robots.txt and rate limits
5. **Resource Management**: Efficient memory usage and cleanup

## Supported Content Types

- HTML pages and articles
- Documentation sites
- Forum discussions and Q&A
- Code repositories and examples
- News articles and blogs
- Academic papers and research

## Troubleshooting

### Common Issues

1. **Playwright Installation**: Run `playwright install` if browsers missing
2. **Memory Usage**: Reduce `max_concurrent` for large batch operations
3. **Rate Limiting**: Increase delays if getting blocked
4. **JavaScript Sites**: Enable JavaScript execution in Playwright settings

### Performance Optimization

- Use `batch_scrape_urls()` for multiple URLs
- Configure appropriate concurrency limits
- Enable content caching for repeated scraping
- Use Firecrawl API for better content extraction

## Development

The web scraper is integrated into Memory-Server's main codebase:

- **Service Classes**: `api/utils/web_scraper.py`
- **API Routes**: `api/routers/web_search.py`
- **Tests**: `tests/integration/test_web_search_endpoints.py`

## API Keys Setup

```bash
# Set environment variables
export SERPER_API_KEY="your-serper-key"
export FIRECRAWL_API_KEY="your-firecrawl-key"

# Or add to .env file
echo "SERPER_API_KEY=your-serper-key" >> .env
echo "FIRECRAWL_API_KEY=your-firecrawl-key" >> .env
```

## License

Part of Memory-Server project - MIT License