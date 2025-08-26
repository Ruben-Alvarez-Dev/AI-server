import os
import sys
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
import html2text

# --- Configuration ---
# The URL is now passed as a command-line argument.
# Example: python3 scraper.py https://r2r-docs.sciphi.ai/

# --- Core Logic ---

async def get_all_links_from_page(page, base_url):
    """
    Fetches all unique links from a page after it has loaded.
    """
    try:
        await page.goto(base_url, wait_until="networkidle")
        
        links = set()
        link_elements = await page.query_selector_all('a[href]')
        
        for link_element in link_elements:
            href = await link_element.get_attribute('href')
            full_url = urljoin(base_url, href)
            
            # Only process links within the same domain and that are not anchors
            if full_url.startswith(base_url) and "#" not in full_url:
                links.add(full_url)
        
        return list(links)
    except Exception as e:
        print(f"Error fetching links from {base_url}: {e}")
        return []

def html_to_markdown(html_content):
    """
    Converts HTML content to Markdown.
    """
    converter = html2text.HTML2Text()
    converter.body_width = 0
    return converter.handle(html_content)

async def main(url):
    """
    Main function to orchestrate the download and conversion process.
    """
    parsed_url = urlparse(url)
    filename_base = parsed_url.netloc.replace('.', '_') + parsed_url.path.replace('/', '_')
    if not filename_base.strip():
        filename_base = "downloaded_docs"
    
    output_filepath = os.path.join(os.getcwd(), filename_base.strip('_') + ".md")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print(f"Starting to download documentation from {url}...")
        urls_to_download = await get_all_links_from_page(page, url)
        
        if not urls_to_download:
            print("No links found after rendering. Please check the URL.")
            await browser.close()
            return

        with open(output_filepath, "w", encoding="utf-8") as md_file:
            for doc_url in urls_to_download:
                try:
                    await page.goto(doc_url, wait_until="networkidle")
                    title = await page.title()
                    md_file.write(f"# {title}\n\n")
                    html_content = await page.content()
                    markdown_content = html_to_markdown(html_content)
                    md_file.write(markdown_content)
                    md_file.write("\n\n---\n\n")
                    print(f"Successfully processed: {doc_url}")
                except Exception as e:
                    print(f"Error processing {doc_url}: {e}")

        await browser.close()
    print(f"Download and conversion complete. Output file: {output_filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scraper.py <URL>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    asyncio.run(main(base_url))
