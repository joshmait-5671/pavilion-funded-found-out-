"""Use Claude to qualify funding announcements and extract structured company info."""
import json
import logging
import anthropic

logger = logging.getLogger(__name__)


def qualify_companies(search_results: list[dict], client: anthropic.Anthropic) -> list[dict]:
    """
    Pass raw search results to Claude for qualification.
    Returns list of dicts: company_name, funding_amount, funding_stage,
    website_url, description, news_url.
    """
    if not search_results:
        return []

    results_text = "\n\n".join([
        f"[{i+1}] Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(search_results[:40])
    ])

    prompt = f"""You are filtering news search results to find AI/tech startup funding announcements.

SEARCH RESULTS:
{results_text}

YOUR TASK:
Identify results that describe a tech or AI startup receiving VC or PE funding.

QUALIFICATION CRITERIA:
- Company type: tech startup, AI company, SaaS, software product — NOT a fund raising LP capital, NOT a non-profit, NOT a physical goods company
- Funding range: between $5M and $40M (skip if unclear or outside this range)
- Funding type: VC or PE backed — Series Seed, Series A, Series B qualify; debt financing and grants do not
- Must be a real company building a product or platform

For each qualified company, extract:
- company_name: The startup's name (string)
- funding_amount: Amount in millions as a number (e.g. 12.5)
- funding_stage: "seed", "series_a", "series_b", or "other"
- website_url: Their company homepage (infer from company name if not stated — e.g. "Acme AI" → "https://acmeai.com")
- description: 1-2 sentences on what the company does and who their customer is
- news_url: The article URL

Return a JSON array only — no other text, no markdown fences.
Return max 10 results. Prioritize cases where funding amount is clear and the company's product is clear.
If no results qualify, return []."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        companies = json.loads(text)
        logger.info(f"Qualifier: {len(companies)} companies qualified from {len(search_results)} results")
        return companies
    except Exception as e:
        logger.error(f"Failed to parse qualifier response: {e}\nRaw: {response.content[0].text[:300]}")
        return []
