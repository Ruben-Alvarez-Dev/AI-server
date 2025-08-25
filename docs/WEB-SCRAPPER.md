# 🕷️ WEB-SCRAPPER

**Documentation Scraping Tool for RAG Integration**

---

## 📖 Overview

The Web-Scrapper is a Python tool that downloads and converts website documentation to Markdown format for RAG (Retrieval-Augmented Generation) integration. It uses Playwright to handle modern dynamic websites.

## 📁 Location

```
AI-server/
└── tools/
    └── web-scrapper/
        ├── scraper.py       # Main scraping script
        ├── README.md        # Usage instructions
        └── pdf_env/         # Python virtual environment
```

## 🔗 Dependencies

- **Python 3**: System requirement
- **Playwright**: Web scraping with dynamic content support
- **html2text**: HTML to Markdown conversion
- **R2R Integration**: Output feeds into RAG system

## 🚀 Usage

### 1. Activate Environment
```bash
cd tools/web-scrapper
source pdf_env/bin/activate
```

### 2. Run Scraper
```bash
python3 scraper.py https://example-docs.com/
```

### 3. Output
Creates a Markdown file: `example-docs_com.md`

## ⚙️ How It Works

1. **Crawling**: Discovers all links within the same domain
2. **Content Extraction**: Downloads each page using Playwright
3. **Conversion**: Converts HTML to clean Markdown
4. **Consolidation**: Combines all pages into a single file

## 🎯 Integration with RAG

### Manual Integration
```bash
# 1. Scrape documentation
python3 scraper.py https://docs.example.com/

# 2. Move to RAG data directory
mv docs_example_com.md ../../llm-server/rag_data/

# 3. Restart servers to index new content
../../start_servers.sh
```

### Automatic Integration (Future)
The scraper could be integrated directly with R2R for automatic indexing.

## 🔧 Configuration

### Supported Sites
- Documentation sites with internal linking
- Sites with consistent URL structure
- Modern sites requiring JavaScript (via Playwright)

### Limitations
- Same-domain links only
- No authentication support
- Memory-intensive for large sites

## 📊 Example Use Cases

1. **API Documentation**: OpenAI, Anthropic, etc.
2. **Framework Docs**: React, Vue, Angular
3. **Library Docs**: Python, JavaScript libraries
4. **Internal Documentation**: Company wikis, guides

## 🛠️ Maintenance

### Update Dependencies
```bash
cd tools/web-scrapper
source pdf_env/bin/activate
pip install --upgrade playwright html2text
```

### Troubleshooting
- **Timeout Issues**: Increase wait time in script
- **Missing Content**: Check if site requires authentication
- **Large Files**: Consider chunking for RAG processing

---

**Location**: `tools/web-scrapper/`
**Dependencies**: R2R RAG System
**Integration**: Manual → RAG data directory