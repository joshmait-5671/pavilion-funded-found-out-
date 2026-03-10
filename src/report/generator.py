"""
Generate the Funded & Found Out LinkedIn carousel PDF.

Each slide is rendered as a 1080x1080 PNG via Playwright,
then all slides are combined into a single PDF via Pillow.
"""
from __future__ import annotations
import asyncio
import base64
import html as html_lib
import io
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

SLIDE_W = 1080
SLIDE_H = 1080

GRADE_COLORS = {
    'A': '#22c55e',
    'B': '#3b82f6',
    'C': '#f59e0b',
    'D': '#ef4444',
}

DIMENSION_LABELS = {
    'centricity': 'Centricity',
    'legibility': 'Legibility',
    'edge': 'Edge',
    'argument': 'Argument',
    'recall': 'Recall',
}

BASE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1080px; height: 1080px; overflow: hidden;
  background: #0a0a0a;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
}
"""


# ─── SLIDE BUILDERS ───────────────────────────────────────────────────────────

def build_intro_slide(week_label: str, company_count: int) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{BASE_CSS}
body {{
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center; padding: 80px;
}}
.eyebrow {{
  font-size: 12px; font-weight: 700; letter-spacing: 3px;
  color: #ff6b35; text-transform: uppercase; margin-bottom: 28px;
}}
.title {{
  font-size: 78px; font-weight: 800; color: #fff;
  line-height: 0.95; margin-bottom: 28px; letter-spacing: -3px;
}}
.title em {{ color: #ff6b35; font-style: normal; }}
.subtitle {{
  font-size: 20px; color: #777; font-weight: 300; line-height: 1.5;
  max-width: 560px; margin-bottom: 48px;
}}
.week {{ color: #444; font-size: 13px; font-weight: 500; letter-spacing: 1px; margin-bottom: 36px; }}
.badges {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 48px; }}
.badge {{
  background: #141414; border: 1px solid #252525;
  border-radius: 6px; padding: 8px 16px;
  font-size: 13px; color: #666; font-weight: 500;
}}
.badge b {{ color: #ff6b35; }}
.byline {{ font-size: 13px; color: #333; letter-spacing: 1px; }}
</style>
</head><body>
  <div class="eyebrow">Weekly AI Marketing Report</div>
  <div class="title">Funded &amp;<br><em>Found Out.</em></div>
  <div class="subtitle">{company_count} newly funded AI companies,<br>graded on their marketing.</div>
  <div class="week">{week_label}</div>
  <div class="badges">
    <div class="badge"><b>C</b>entricity</div>
    <div class="badge"><b>L</b>egibility</div>
    <div class="badge"><b>E</b>dge</div>
    <div class="badge"><b>A</b>rgument</div>
    <div class="badge"><b>R</b>ecall</div>
  </div>
  <div class="byline">by Josh Mait &nbsp;·&nbsp; Pavilion</div>
</body></html>"""


def _embed_screenshot(path: str) -> str:
    """
    Resize the tall screenshot to a compact JPEG and embed as base64.
    The image is 1440x1800 — displayed at full width it naturally shows
    the top of the page (nav, logo, hero) without any cropping needed.
    """
    placeholder = '<div style="width:100%;height:100%;background:#111;border-radius:8px;"></div>'
    if not path or not Path(path).exists():
        return placeholder
    try:
        img = Image.open(path).convert('RGB')
        # Resize to max 900px wide — keeps aspect ratio, reduces base64 size
        img.thumbnail((900, 1125), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return (
            f'<img src="data:image/jpeg;base64,{b64}" '
            f'style="width:100%;display:block;border-radius:8px;" />'
        )
    except Exception as e:
        logger.warning(f"Screenshot embed failed for {path}: {e}")
        return placeholder


def build_overview_slide(
    company: dict,
    evaluation: dict,
    screenshot_paths: list,
    slide_num: int,
    total: int,
) -> str:
    stage = company.get('funding_stage', '').replace('_', ' ').title()
    funding_badge = f"${company.get('funding_amount', '?')}M {stage}"
    company_name = html_lib.escape(company.get('company_name', ''))
    website_url = html_lib.escape(company.get('website_url', ''))
    paragraph = html_lib.escape(evaluation.get('overall_paragraph', company.get('description', '')))
    if len(paragraph) > 280:
        paragraph = paragraph[:280] + '…'

    screenshot_html = _embed_screenshot(screenshot_paths[0] if screenshot_paths else '')

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{BASE_CSS}
body {{ display: flex; flex-direction: column; padding: 48px; overflow: hidden; }}
.topbar {{
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 18px; flex-shrink: 0;
}}
.counter {{ font-size: 11px; color: #444; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; }}
.funding {{
  background: #ff6b35; color: #fff;
  border-radius: 100px; padding: 5px 16px;
  font-size: 13px; font-weight: 700;
}}
.name {{
  font-size: 48px; font-weight: 800; color: #fff;
  line-height: 1.0; letter-spacing: -1.5px; margin-bottom: 4px; flex-shrink: 0;
}}
.url {{ font-size: 12px; color: #444; margin-bottom: 12px; flex-shrink: 0; }}
.paragraph {{
  font-size: 14px; color: #aaa; line-height: 1.6; font-weight: 300;
  margin-bottom: 18px; flex-shrink: 0;
}}
.screenshot-wrap {{
  flex: 1; overflow: hidden;
  border-radius: 8px;
  border: 2px solid #ff6b35;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}}
</style>
</head><body>
  <div class="topbar">
    <div class="counter">Company {slide_num} of {total}</div>
    <div class="funding">{html_lib.escape(funding_badge)}</div>
  </div>
  <div class="name">{company_name}</div>
  <div class="url">{website_url}</div>
  <div class="paragraph">{paragraph}</div>
  <div class="screenshot-wrap">{screenshot_html}</div>
</body></html>"""


def build_grades_slide(company: dict, evaluation: dict) -> str:
    company_name = html_lib.escape(company.get('company_name', ''))
    headline = html_lib.escape(evaluation.get('headline', f"Grading {company.get('company_name', '')}"))
    grades = evaluation.get('grades', {})

    rows = ''
    for key in ['centricity', 'legibility', 'edge', 'argument', 'recall']:
        data = grades.get(key, {})
        grade = data.get('grade', 'C')
        explanation = html_lib.escape(data.get('explanation', ''))
        if len(explanation) > 195:
            explanation = explanation[:195] + '…'
        color = GRADE_COLORS.get(grade, '#888')
        label = DIMENSION_LABELS.get(key, key.title())

        rows += f"""
<div style="display:flex;gap:18px;padding:13px 0;border-bottom:1px solid #181818;align-items:flex-start;">
  <div style="width:42px;height:42px;flex-shrink:0;border-radius:7px;
              background:{color}18;border:1px solid {color}40;
              display:flex;align-items:center;justify-content:center;
              font-size:20px;font-weight:800;color:{color};">{grade}</div>
  <div style="flex:1;min-width:0;">
    <div style="font-size:11px;font-weight:700;color:{color};letter-spacing:1.5px;
                text-transform:uppercase;margin-bottom:3px;">{label}</div>
    <div style="font-size:14px;color:#888;line-height:1.5;font-weight:300;">{explanation}</div>
  </div>
</div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{BASE_CSS}
body {{ display: flex; flex-direction: column; padding: 52px; }}
.label {{
  font-size: 11px; color: #ff6b35; font-weight: 700;
  letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px;
}}
.headline {{
  font-size: 26px; font-weight: 700; color: #fff;
  line-height: 1.3; letter-spacing: -0.3px; margin-bottom: 28px;
  max-width: 900px;
}}
.footer {{
  margin-top: auto; padding-top: 16px;
  font-size: 11px; color: #2a2a2a; letter-spacing: 1.5px; text-transform: uppercase;
}}
</style>
</head><body>
  <div class="label">CLEAR Report &nbsp;·&nbsp; {company_name}</div>
  <div class="headline">"{headline}"</div>
  <div style="display:flex;flex-direction:column;flex:1;">{rows}</div>
  <div class="footer">C · L · E · A · R &nbsp;|&nbsp; Funded &amp; Found Out by Josh Mait</div>
</body></html>"""


def build_outro_slide() -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{BASE_CSS}
body {{
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center; padding: 80px;
}}
.title {{
  font-size: 64px; font-weight: 800; color: #fff;
  letter-spacing: -2px; line-height: 1.0; margin-bottom: 24px;
}}
.title em {{ color: #ff6b35; font-style: normal; }}
.body {{
  font-size: 18px; color: #666; line-height: 1.65;
  max-width: 620px; margin-bottom: 48px; font-weight: 300;
}}
.box {{
  border: 1px solid #1f1f1f; border-radius: 14px;
  padding: 28px 44px; margin-bottom: 48px;
  font-size: 16px; color: #888; line-height: 1.7;
}}
.box strong {{ color: #ccc; }}
.footer {{ font-size: 12px; color: #2a2a2a; letter-spacing: 1px; }}
</style>
</head><body>
  <div class="title">That&apos;s a<br><em>wrap.</em></div>
  <div class="body">Every funded AI company is making a bet. The ones who get marketing right will compound that investment. The ones who don't will struggle to explain why they matter.</div>
  <div class="box">
    <strong>Follow for more.</strong><br>
    Every week: 5 companies, 5 grades, no filter.<br>
    By Josh Mait &nbsp;·&nbsp; Head of Marketing, Pavilion.
  </div>
  <div class="footer">funded-and-found-out &nbsp;·&nbsp; joinpavilion.com</div>
</body></html>"""


# ─── RENDERING ─────────────────────────────────────────────────────────────────

async def _render_slide_async(html: str, output_path: Path) -> bool:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={'width': SLIDE_W, 'height': SLIDE_H})
            await page.set_content(html, wait_until='networkidle')
            await asyncio.sleep(0.3)
            await page.screenshot(path=str(output_path), full_page=False)
            return True
        except Exception as e:
            logger.error(f"Slide render failed: {e}")
            return False
        finally:
            await browser.close()


def render_slide(html: str, output_path: Path) -> bool:
    return asyncio.run(_render_slide_async(html, output_path))


def combine_to_pdf(slide_paths: list[Path], pdf_path: Path) -> bool:
    """Combine PNG slides into a single PDF using Pillow."""
    try:
        images = []
        for p in slide_paths:
            if p.exists():
                images.append(Image.open(p).convert('RGB'))

        if not images:
            logger.error("No slides to combine")
            return False

        images[0].save(
            str(pdf_path),
            format='PDF',
            save_all=True,
            append_images=images[1:],
            resolution=150,
        )
        logger.info(f"PDF saved: {pdf_path.name} ({len(images)} slides)")
        return True
    except Exception as e:
        logger.error(f"PDF creation failed: {e}")
        return False


# ─── MAIN ENTRY ────────────────────────────────────────────────────────────────

def generate_carousel(
    companies: list[dict],
    evaluations: list[dict],
    screenshot_paths: list[list[str]],
    output_dir: Path,
    slides_dir: Path,
) -> Path | None:
    """
    Build the full LinkedIn carousel PDF.
    Returns the PDF path or None on failure.
    """
    slides_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    week_label = datetime.now().strftime("Week of %B %d, %Y")
    date_str = datetime.now().strftime("%Y-%m-%d")
    pdf_path = output_dir / f"funded-and-found-out-{date_str}.pdf"

    all_slide_paths: list[Path] = []

    # 1. Intro
    intro_path = slides_dir / "00_intro.png"
    if render_slide(build_intro_slide(week_label, len(companies)), intro_path):
        all_slide_paths.append(intro_path)
        logger.info("Rendered intro slide")

    # 2. Per-company slides
    for i, (company, evaluation, shots) in enumerate(zip(companies, evaluations, screenshot_paths)):
        if not evaluation:
            logger.warning(f"Skipping {company.get('company_name')} — no evaluation")
            continue

        # Slide A: Overview + 2x2 screenshot grid
        overview_path = slides_dir / f"{i+1:02d}a_overview.png"
        if render_slide(
            build_overview_slide(company, evaluation, shots, i + 1, len(companies)),
            overview_path,
        ):
            all_slide_paths.append(overview_path)

        # Slide B: CLEAR grades
        grades_path = slides_dir / f"{i+1:02d}b_grades.png"
        if render_slide(build_grades_slide(company, evaluation), grades_path):
            all_slide_paths.append(grades_path)

        logger.info(f"Rendered slides for {company.get('company_name')}")

    # 3. Outro
    outro_path = slides_dir / "99_outro.png"
    if render_slide(build_outro_slide(), outro_path):
        all_slide_paths.append(outro_path)
        logger.info("Rendered outro slide")

    logger.info(f"Total slides: {len(all_slide_paths)}")

    if combine_to_pdf(all_slide_paths, pdf_path):
        return pdf_path
    return None
