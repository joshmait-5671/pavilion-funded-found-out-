"""Take a single tall screenshot of a company's homepage using Playwright."""
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def _take_screenshots_async(url: str, output_dir: Path, company_slug: str) -> list[str]:
    """
    Take one tall screenshot of the homepage (top 1800px).
    Returns a list with a single file path.
    """
    from playwright.async_api import async_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                viewport={'width': 1440, 'height': 1800},
                user_agent=(
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ),
            )
            page = await context.new_page()

            # Navigate — fallback from networkidle to domcontentloaded
            try:
                await page.goto(url, wait_until='networkidle', timeout=20000)
            except Exception:
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                except Exception as e:
                    logger.warning(f"Navigation failed for {url}: {e}")
                    return paths

            await asyncio.sleep(2)  # Let animations and fonts settle

            shot_path = output_dir / f"{company_slug}.png"
            await page.screenshot(
                path=str(shot_path),
                clip={'x': 0, 'y': 0, 'width': 1440, 'height': 1800},
            )
            paths.append(str(shot_path))
            logger.info(f"Screenshot saved: {shot_path.name}")

        except Exception as e:
            logger.warning(f"Screenshot failed for {url}: {e}")
        finally:
            await browser.close()

    return paths


def take_screenshots(url: str, output_dir: Path, company_slug: str) -> list[str]:
    """Sync wrapper around async screenshot function."""
    return asyncio.run(_take_screenshots_async(url, output_dir, company_slug))
