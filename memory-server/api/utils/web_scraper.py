"""
Web Scraper Service for Memory-Server
Adapts the existing Playwright scraper with Memory-Server integration
"""

import os
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import tempfile

from playwright.async_api import async_playwright
import html2text

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger("web-scraper")
config = get_config()

@dataclass
class ScrapingResult:
    success: bool
    content: str
    pages_scraped: int
    urls_processed: List[str]
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class WebScraperService:
    """Enhanced web scraper based on existing Playwright scraper"""
    
    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        
    async def scrape_website(
        self,
        url: str,
        max_pages: int = 10,
        include_pdfs: bool = True,
        include_external: bool = False
    ) -> ScrapingResult:
        """
        Scrape website content using Playwright
        
        Args:
            url: Base URL to scrape
            max_pages: Maximum number of pages to scrape
            include_pdfs: Whether to include PDF links
            include_external: Whether to include external domain links
        """
        try:
            logger.info(f"Starting web scraping: {url}")
            
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Get all links from main page
                urls_to_process = await self._get_all_links_from_page(
                    page, url, include_external, include_pdfs
                )
                
                if not urls_to_process:
                    await browser.close()
                    return ScrapingResult(
                        success=False,
                        content="",
                        pages_scraped=0,
                        urls_processed=[],
                        error="No links found to scrape"
                    )
                
                # Limit pages to scrape
                urls_to_process = urls_to_process[:max_pages]
                
                # Scrape content from each URL
                scraped_content = []
                processed_urls = []
                
                for doc_url in urls_to_process:
                    try:
                        await page.goto(doc_url, wait_until="networkidle", timeout=30000)
                        title = await page.title()
                        html_content = await page.content()
                        
                        # Convert to markdown
                        markdown_content = self._html_to_markdown(html_content)
                        
                        # Add structured content
                        page_content = f"# {title}\n\n"
                        page_content += f"**URL:** {doc_url}\n\n"
                        page_content += markdown_content
                        page_content += "\n\n---\n\n"
                        
                        scraped_content.append(page_content)
                        processed_urls.append(doc_url)
                        
                        logger.info(f"Successfully scraped: {doc_url}")
                        
                    except Exception as e:
                        logger.warning(f"Error scraping {doc_url}: {e}")
                        continue
                
                await browser.close()
                
                if not scraped_content:
                    return ScrapingResult(
                        success=False,
                        content="",
                        pages_scraped=0,
                        urls_processed=[],
                        error="No content could be scraped"
                    )
                
                # Combine all content
                full_content = "\n".join(scraped_content)
                
                metadata = {
                    "base_url": url,
                    "total_links_found": len(urls_to_process),
                    "successfully_scraped": len(processed_urls),
                    "include_pdfs": include_pdfs,
                    "include_external": include_external
                }
                
                logger.info(f"Web scraping completed: {len(processed_urls)} pages from {url}")
                
                return ScrapingResult(
                    success=True,
                    content=full_content,
                    pages_scraped=len(processed_urls),
                    urls_processed=processed_urls,
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error(f"Web scraping failed for {url}: {e}")
            return ScrapingResult(
                success=False,
                content="",
                pages_scraped=0,
                urls_processed=[],
                error=str(e)
            )
    
    async def _get_all_links_from_page(
        self, 
        page, 
        base_url: str, 
        include_external: bool = False,
        include_pdfs: bool = True
    ) -> List[str]:
        """Extract all relevant links from a page"""
        try:
            await page.goto(base_url, wait_until="networkidle", timeout=30000)
            
            links = set()
            link_elements = await page.query_selector_all('a[href]')
            
            base_domain = urlparse(base_url).netloc
            
            for link_element in link_elements:
                href = await link_element.get_attribute('href')
                if not href:
                    continue
                    
                full_url = urljoin(base_url, href)
                parsed_url = urlparse(full_url)
                
                # Skip fragments/anchors
                if "#" in href and not parsed_url.path:
                    continue
                
                # Skip javascript links
                if full_url.startswith('javascript:'):
                    continue
                
                # Check domain restrictions
                if not include_external and parsed_url.netloc != base_domain:
                    continue
                
                # Check PDF inclusion
                if full_url.lower().endswith('.pdf') and not include_pdfs:
                    continue
                
                # Only include HTTP/HTTPS links
                if parsed_url.scheme in ['http', 'https']:
                    links.add(full_url)
            
            return list(links)
            
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
            return []
    
    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to markdown"""
        try:
            return self.html_converter.handle(html_content)
        except Exception as e:
            logger.warning(f"Error converting HTML to markdown: {e}")
            return html_content
    
    async def scrape_single_page(self, url: str) -> ScrapingResult:
        """Scrape a single page"""
        return await self.scrape_website(url, max_pages=1)
    
    async def scrape_forum_posts(
        self, 
        forum_url: str, 
        max_posts: int = 50,
        keywords: Optional[List[str]] = None
    ) -> ScrapingResult:
        """
        Specialized scraping for forums (Reddit, Discord, etc.)
        """
        try:
            logger.info(f"Scraping forum posts from: {forum_url}")
            
            # This is a simplified version - can be extended for specific forum types
            result = await self.scrape_website(
                url=forum_url,
                max_pages=min(max_posts, 20),  # Limit for performance
                include_external=False
            )
            
            if result.success and keywords:
                # Filter content by keywords
                filtered_content = self._filter_content_by_keywords(result.content, keywords)
                result.content = filtered_content
            
            return result
            
        except Exception as e:
            logger.error(f"Forum scraping failed for {forum_url}: {e}")
            return ScrapingResult(
                success=False,
                content="",
                pages_scraped=0,
                urls_processed=[],
                error=str(e)
            )
    
    def _filter_content_by_keywords(self, content: str, keywords: List[str]) -> str:
        """Filter content to include only sections with relevant keywords"""
        lines = content.split('\n')
        filtered_lines = []
        context_lines = 5  # Lines to include around matches
        
        for i, line in enumerate(lines):
            if any(keyword.lower() in line.lower() for keyword in keywords):
                # Include context around the match
                start_idx = max(0, i - context_lines)
                end_idx = min(len(lines), i + context_lines + 1)
                
                for j in range(start_idx, end_idx):
                    if lines[j] not in filtered_lines:
                        filtered_lines.append(lines[j])
        
        return '\n'.join(filtered_lines) if filtered_lines else content
    
    async def get_page_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata from a page"""
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Extract metadata
                title = await page.title()
                
                # Try to get meta description
                description_element = await page.query_selector('meta[name="description"]')
                description = ""
                if description_element:
                    description = await description_element.get_attribute('content') or ""
                
                # Try to get meta keywords
                keywords_element = await page.query_selector('meta[name="keywords"]')
                keywords = ""
                if keywords_element:
                    keywords = await keywords_element.get_attribute('content') or ""
                
                await browser.close()
                
                return {
                    "title": title,
                    "description": description,
                    "keywords": keywords.split(',') if keywords else [],
                    "url": url
                }
                
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {e}")
            return {"url": url, "title": "", "description": "", "keywords": []}