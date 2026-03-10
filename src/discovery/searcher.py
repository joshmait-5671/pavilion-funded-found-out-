"""Search for recent AI/tech funding announcements using DuckDuckGo."""
import time
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# Varied queries to maximize coverage across sources
SEARCH_QUERIES = [
    "AI startup raises million series funding 2025 site:techcrunch.com",
    "artificial intelligence company funding announcement million 2025 site:techcrunch.com",
    "AI SaaS startup raises million venture 2025 site:venturebeat.com",
    "machine learning startup funding series 2025 site:venturebeat.com",
    "AI company raises million seed series 2025 site:axios.com",
    "tech AI startup funding announcement million 2025 site:businesswire.com",
    "AI startup raises venture capital million 2025",
    "\"raised\" \"million\" AI startup series 2025",
]


def search_funding_news(max_results_per_query: int = 8) -> list[dict]:
    """
    Search DuckDuckGo for recent AI/tech funding announcements.
    Uses timelimit='w' to target the past week only.
    Returns a deduplicated list of raw search results.
    """
    results = []
    seen_urls = set()

    with DDGS() as ddgs:
        for query in SEARCH_QUERIES:
            try:
                logger.info(f"Searching: {query[:70]}...")
                time.sleep(1.5)  # Polite rate limiting

                hits = ddgs.text(
                    query,
                    max_results=max_results_per_query,
                    timelimit='w',  # Past week only
                )

                for r in (hits or []):
                    url = r.get('href', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results.append({
                            'title': r.get('title', ''),
                            'url': url,
                            'snippet': r.get('body', ''),
                        })

            except Exception as e:
                logger.warning(f"Search failed for query: {e}")
                continue

    logger.info(f"Discovery: {len(results)} raw results across {len(SEARCH_QUERIES)} queries")
    return results
