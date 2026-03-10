"""Evaluate company websites using the CLEAR framework."""
from __future__ import annotations
import json
import logging
import anthropic

logger = logging.getLogger(__name__)

CLEAR_FRAMEWORK = """
The CLEAR Framework — 5 dimensions of AI startup marketing effectiveness:

1. CENTRICITY (Customer Centricity)
   Do they lead with the customer's problems and outcomes, or with their own product and features?
   A = Customer is the hero everywhere. D = "We built X" language throughout.

2. LEGIBILITY (Use Case Legibility)
   Are the use cases specific, distinct, and actionable? Can a visitor immediately
   understand who this is for and what job it does?
   A = Named personas, concrete scenarios. D = Vague descriptions that fit any AI company.

3. EDGE (Competitive Edge)
   Have they explained what makes them different from ChatGPT, general LLMs, or direct competitors?
   Do they have a clear "why not just use GPT-4" answer?
   A = Crisp, confident differentiation. D = Indistinguishable from 50 other AI companies.

4. ARGUMENT (Point of View)
   Have they articulated a POV or argument for why they exist and why now?
   Do they have an opinion about the market?
   A = Clear thesis, confident stance, memorable argument. D = Feature list with no perspective.

5. RECALL (Brand Recall)
   Is the brand name interesting and memorable? Is the verbal and visual identity distinctive?
   Will someone remember this brand after one visit?
   A = Sticky, original, you'd tell a friend. D = Forgettable, generic, sounds like every other AI startup.
"""


def evaluate_company(company: dict, website_content: dict, client: anthropic.Anthropic) -> dict | None:
    """
    Evaluate a company's website using the CLEAR framework.
    Returns structured evaluation dict or None on failure.
    """
    content_block = f"""
Company: {company['company_name']}
Funding: ${company.get('funding_amount', '?')}M — {company.get('funding_stage', '').replace('_', ' ').title()}
Known description: {company.get('description', 'N/A')}

Website: {website_content.get('url', '')}
Page title: {website_content.get('title', '')}
Meta description: {website_content.get('meta_description', '')}
Hero headings: {website_content.get('hero_text', '')}

Full page text:
{website_content.get('full_text', '')[:5000]}
"""

    prompt = f"""You are a senior B2B marketing analyst writing a weekly LinkedIn series called "Funded & Found Out."
You evaluate newly funded AI startups on how well they market themselves. Your audience is marketing and revenue leaders.
You are honest, direct, and occasionally witty. You cite specific evidence. You don't grade on a curve.

{CLEAR_FRAMEWORK}

COMPANY TO EVALUATE:
{content_block}

YOUR OUTPUT:
Evaluate this company on all 5 CLEAR dimensions. For each:
- Assign a grade: A, B, C, or D
- Write exactly 2-3 sentences with specific evidence from what you read (quote their actual copy when helpful)

Also write:
- headline: A punchy 8-14 word sentence summarizing your overall take. Can be slightly wry or direct.
- overall_paragraph: 4-6 sentences. Start with what the company does and their funding. Then your honest marketing take.
  Write in second person to Josh (the author), who will lightly edit this before posting.

Return ONLY valid JSON in this exact structure — no markdown, no extra text:
{{
  "headline": "...",
  "overall_paragraph": "...",
  "grades": {{
    "centricity": {{"grade": "A/B/C/D", "explanation": "2-3 sentences with specific evidence."}},
    "legibility": {{"grade": "A/B/C/D", "explanation": "2-3 sentences with specific evidence."}},
    "edge": {{"grade": "A/B/C/D", "explanation": "2-3 sentences with specific evidence."}},
    "argument": {{"grade": "A/B/C/D", "explanation": "2-3 sentences with specific evidence."}},
    "recall": {{"grade": "A/B/C/D", "explanation": "2-3 sentences with specific evidence."}}
  }}
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        evaluation = json.loads(text)

        grades = [evaluation['grades'][d]['grade'] for d in ['centricity', 'legibility', 'edge', 'argument', 'recall']]
        logger.info(f"Evaluated {company['company_name']}: {grades}")
        return evaluation

    except Exception as e:
        logger.error(f"Failed to parse evaluation for {company.get('company_name', '?')}: {e}")
        logger.error(f"Raw response: {response.content[0].text[:400]}")
        return None
