"""Scrape company website text content for CLEAR analysis."""
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def scrape_website(url: str, timeout: int = 15) -> dict:
    """
    Fetch and parse a company's homepage.
    Returns: {url, title, meta_description, hero_text, full_text, success}
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Remove noise
        for tag in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript', 'head']):
            tag.decompose()

        # Title
        title = ''
        if soup.title:
            title = soup.title.get_text(strip=True)

        # Meta description
        meta_desc = ''
        meta_tag = (
            soup.find('meta', attrs={'name': 'description'}) or
            soup.find('meta', attrs={'property': 'og:description'})
        )
        if meta_tag:
            meta_desc = meta_tag.get('content', '')

        # Hero headings: h1, h2 near the top
        hero_parts = []
        for tag in soup.find_all(['h1', 'h2', 'h3'])[:8]:
            text = tag.get_text(strip=True)
            if text and len(text) > 4:
                hero_parts.append(text)

        # Full visible text (first 6000 chars is usually enough)
        full_text = ' '.join(soup.get_text(separator=' ', strip=True).split())[:6000]

        return {
            'url': url,
            'title': title,
            'meta_description': meta_desc,
            'hero_text': ' | '.join(hero_parts),
            'full_text': full_text,
            'success': True,
        }

    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return {
            'url': url,
            'title': '',
            'meta_description': '',
            'hero_text': '',
            'full_text': '',
            'success': False,
        }
