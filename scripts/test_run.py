#!/usr/bin/env python3
"""
Test the full analysis + PDF pipeline with a specific company.
Use this to validate everything works before the first real run.

Usage:
    python scripts/test_run.py --url https://example.com --name "Company Name" --funding 15
    python scripts/test_run.py --url https://cursor.com --name "Cursor" --funding 20
"""
import sys
import os
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import anthropic
from src.analysis.scraper import scrape_website
from src.analysis.screenshotter import take_screenshots
from src.analysis.evaluator import evaluate_company
from src.report.generator import generate_carousel

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

BASE_DIR = Path(__file__).parent.parent


def main():
    parser = argparse.ArgumentParser(description='Test Funded & Found Out on a single company')
    parser.add_argument('--url', required=True, help='Company website URL')
    parser.add_argument('--name', required=True, help='Company name')
    parser.add_argument('--funding', type=float, default=10.0, help='Funding in millions (default: 10)')
    parser.add_argument('--stage', default='series_a', help='Funding stage (default: series_a)')
    args = parser.parse_args()

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    company = {
        'company_name': args.name,
        'website_url': args.url,
        'funding_amount': args.funding,
        'funding_stage': args.stage,
        'description': f'Test run for {args.name}',
    }

    print(f"\n🧪 Test run: {args.name} ({args.url})\n")

    # Scrape
    print("1. Scraping website...")
    content = scrape_website(args.url)
    status = "✓" if content['success'] else "⚠ (partial)"
    print(f"   {status} {len(content.get('full_text', ''))} chars extracted")
    print(f"   Title: {content.get('title', 'N/A')}")
    print(f"   Hero: {content.get('hero_text', 'N/A')[:100]}")

    # Screenshots
    print("\n2. Taking screenshots...")
    slug = args.name.lower().replace(' ', '_')[:20]
    shots = take_screenshots(args.url, BASE_DIR / 'screenshots' / 'test', slug)
    print(f"   ✓ {len(shots)} screenshots saved")

    # CLEAR evaluation
    print("\n3. Running CLEAR evaluation...")
    evaluation = evaluate_company(company, content, client)

    if not evaluation:
        print("   ❌ Evaluation failed")
        sys.exit(1)

    print(f"\n   Headline: {evaluation['headline']}")
    print(f"\n   Overview:\n   {evaluation['overall_paragraph'][:300]}...\n")
    print("   CLEAR Grades:")
    for dim in ['centricity', 'legibility', 'edge', 'argument', 'recall']:
        d = evaluation['grades'][dim]
        print(f"   {dim.upper()[:10]:<12} {d['grade']}  {d['explanation'][:80]}...")

    # PDF
    print("\n4. Generating PDF carousel...")
    pdf = generate_carousel(
        companies=[company],
        evaluations=[evaluation],
        screenshot_paths=[shots],
        output_dir=BASE_DIR / 'output',
        slides_dir=BASE_DIR / 'slides' / 'test',
    )

    if pdf:
        print(f"\n✅ Success! PDF saved to:\n   {pdf}")
        print("\nOpen the PDF and verify it looks good before running the full pipeline.")
    else:
        print("\n❌ PDF generation failed — check logs above")
        sys.exit(1)


if __name__ == '__main__':
    main()
