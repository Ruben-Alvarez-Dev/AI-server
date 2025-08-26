# Web Scraper Tool

## 📋 Visión General

**Web Scraper Tool** es una herramienta desarrollada internamente para extraer automáticamente documentación completa de sitios web y convertirla a formato Markdown para ingesta en Memory-Server.

### **Composición Técnica**
- **Lenguaje**: Python 3.13+
- **Engine**: Playwright (Chromium automation)
- **Output**: Markdown unified (.md)
- **Parser**: html2text para conversión HTML→MD
- **Architecture**: Async single-page crawler

### **Propósito de Diseño**
Automatizar la ingesta de documentación técnica completa desde sitios web, especialmente documentación de APIs, frameworks y herramientas para alimentar el sistema RAG de Memory-Server.

## 🏗️ Arquitectura Técnica

### **Core Components**

#### **1. Browser Automation Engine**
```python
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    
    # Full page rendering con JavaScript
    await page.goto(base_url, wait_until="networkidle")
```

**Características:**
- Full Chromium browser automation
- JavaScript execution completa
- Network idle detection para SPA/dynamic content
- Headless operation para performance

#### **2. Link Discovery System**
```python
async def get_all_links_from_page(page, base_url):
    links = set()
    link_elements = await page.query_selector_all('a[href]')
    
    for link_element in link_elements:
        href = await link_element.get_attribute('href')
        full_url = urljoin(base_url, href)
        
        # Domain filtering + anchor filtering
        if full_url.startswith(base_url) and "#" not in full_url:
            links.add(full_url)
    
    return list(links)
```

**Funcionalidades:**
- Same-domain link extraction automática
- Deduplicación de URLs
- Anchor link filtering (#fragments)
- Absolute URL resolution con urljoin()

#### **3. Content Processing Pipeline**
```python
def html_to_markdown(html_content):
    converter = html2text.HTML2Text()
    converter.body_width = 0  # No line wrapping
    return converter.handle(html_content)
```

**Procesamiento:**
- HTML → Markdown conversion
- Preservación de estructura (headings, lists, code)
- Link preservation con markdown format
- No line wrapping para mejor legibilidad

### **Workflow de Scraping**

#### **1. Initialization Phase**
```bash
python3 scraper.py https://docs.example.com/
```

**Proceso:**
1. URL validation y parsing
2. Output filename generation basado en domain
3. Browser instance creation
4. Initial page load con network idle wait

#### **2. Discovery Phase**  
```python
urls_to_download = await get_all_links_from_page(page, url)
print(f"Found {len(urls_to_download)} pages to scrape")
```

**Proceso:**
1. Full page rendering (JavaScript execution)
2. Link extraction de todos los `<a href>` elements
3. URL normalization y filtering
4. Deduplication con Set() data structure

#### **3. Processing Phase**
```python
with open(output_filepath, "w", encoding="utf-8") as md_file:
    for doc_url in urls_to_download:
        await page.goto(doc_url, wait_until="networkidle")
        title = await page.title()
        html_content = await page.content()
        markdown_content = html_to_markdown(html_content)
        md_file.write(f"# {title}\\n\\n{markdown_content}\\n\\n---\\n\\n")
```

**Proceso:**
1. Sequential page processing (no concurrency para evitar rate limiting)
2. Full page load con networkidle wait
3. Title extraction para headings
4. Complete HTML content extraction
5. Markdown conversion con html2text
6. Unified file output con separators

## 🎯 Funcionalidades Específicas

### **1. Domain-Scoped Crawling**
```python
# Solo procesa links del mismo dominio
if full_url.startswith(base_url) and "#" not in full_url:
    links.add(full_url)
```

**Ventajas:**
- Evita crawling externo no deseado
- Mantiene scope de documentación específica
- Previene infinite crawling
- Respeta boundaries del sitio target

### **2. JavaScript-Aware Processing**
```python
await page.goto(doc_url, wait_until="networkidle")
```

**Capacidades:**
- Full SPA (Single Page App) support
- Dynamic content loading
- AJAX request completion waiting
- Modern framework compatibility (React, Vue, Angular)

### **3. Unified Output Generation**
```python
# Estructura de output consistente
md_file.write(f"# {title}\\n\\n")           # Page title
md_file.write(markdown_content)            # Converted content  
md_file.write("\\n\\n---\\n\\n")            # Page separator
```

**Formato:**
- Single markdown file output
- Consistent heading structure
- Clear page separations
- Preserved internal linking

## 📊 Performance Characteristics

### **Processing Speed**
- ~2-5 segundos por página (incluyendo JS rendering)
- Network idle detection añade ~1-2 segundos por página
- Sequential processing para evitar rate limiting
- Memory efficient (no concurrent page loading)

### **Output Efficiency**
- Typical compression: HTML → MD ~60-80% size reduction
- Clean markdown sin artifacts de CSS/JS
- Preserved semantic structure
- Link preservation para navigation

## 🔧 Usage Patterns

### **Documentation Sites**
```bash
# API Documentation
python3 scraper.py https://docs.stripe.com/

# Framework Docs  
python3 scraper.py https://react.dev/

# Internal Tools
python3 scraper.py https://internal-docs.company.com/
```

### **Integration con Memory-Server**
```bash
# 1. Scrape documentation
python3 scraper.py https://docs.example.com/

# 2. Ingest a Memory-Server
curl -X POST http://localhost:8001/api/v1/documents \\
  -F "file=@docs_example_com.md" \\
  -F "workspace=documentation"

# 3. Query via RAG
curl -X POST http://localhost:8001/api/v1/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "how to authenticate API calls", "workspace": "documentation"}'
```

## 🛠️ Configuration Options

### **Output Control**
```python
# Filename generation
filename_base = parsed_url.netloc.replace('.', '_') + parsed_url.path.replace('/', '_')
output_filepath = os.path.join(os.getcwd(), filename_base.strip('_') + ".md")
```

### **HTML2Text Settings**
```python
converter = html2text.HTML2Text()
converter.body_width = 0        # No line wrapping
converter.ignore_links = False  # Preserve links
converter.ignore_images = False # Preserve image references
```

### **Browser Options**
```python
# Extensible para diferentes needs
browser = await p.chromium.launch(
    headless=True,              # Default headless
    slow_mo=0,                  # No artificial delays
    timeout=30000               # 30s timeout per operation
)
```

## 🔒 Security Considerations

### **Domain Restriction**
```python
# Strict same-domain policy
if full_url.startswith(base_url) and "#" not in full_url:
    links.add(full_url)
```

### **Error Handling**
```python
try:
    await page.goto(doc_url, wait_until="networkidle")
    # ... processing
except Exception as e:
    print(f"Error processing {doc_url}: {e}")
    # Continue con siguiente página
```

### **Resource Management**
```python
async with async_playwright() as p:
    # Automatic cleanup de browser resources
    # Exception-safe resource management
    await browser.close()  # Explicit cleanup
```

## 🚀 Installation & Setup

### **Dependencies**
```bash
pip install playwright html2text

# Install browser binaries
playwright install chromium
```

### **Usage**
```bash
cd tools/web-scraper/

# Basic scraping
python3 scraper.py https://docs.target-site.com/

# Output goes to current directory
ls -la *.md
```

## 📈 Extension Opportunities

### **Planned Enhancements**
1. **Concurrent processing** con rate limiting
2. **Content filtering** por CSS selectors
3. **Multi-format output** (JSON, YAML, etc.)
4. **Incremental updates** con change detection
5. **Custom extraction rules** por site type

### **Integration Points**
1. **ATLAS integration** para audit trail
2. **Memory-Server direct API** calls
3. **Scheduler integration** para periodic updates
4. **Webhook support** para automated triggers

---

**Estado**: ✅ Completamente funcional  
**Use Cases**: Documentation ingestion, Knowledge base building  
**Mantenimiento**: Internal AI-Server team  
**Licencia**: MIT (internal use)