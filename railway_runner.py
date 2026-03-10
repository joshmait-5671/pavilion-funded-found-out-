"""
Railway Runner — Funded & Found Out
-------------------------------------
Writes Gmail token from env var, then runs on schedule:
- Monday 9am ET: run full pipeline (discovery → analysis → PDF)
- Wednesday 5pm ET: send email delivery
"""

import os
import sys
import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Write Gmail token from env var ────────────────────────────────────────────
def write_token_from_env():
    token_json = os.environ.get("GMAIL_TOKEN_JSON")
    if token_json:
        token_path = "auth/token.json"
        os.makedirs("auth", exist_ok=True)
        with open(token_path, "w") as f:
            f.write(token_json)
        log.info(f"Wrote Gmail token to {token_path}")
    else:
        log.warning("GMAIL_TOKEN_JSON not set — using existing file if present")

# ── Jobs ──────────────────────────────────────────────────────────────────────
def run_pipeline():
    log.info("Running Funded & Found Out pipeline (Monday)...")
    os.system("python scripts/run_pipeline.py")

def run_delivery():
    log.info("Running Funded & Found Out delivery (Wednesday)...")
    os.system("python scripts/run_delivery.py")

# ── Scheduler ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    write_token_from_env()

    scheduler = BlockingScheduler(timezone="America/New_York")

    # Pipeline: Monday 9am ET
    scheduler.add_job(run_pipeline, "cron", day_of_week="mon", hour=9, minute=0)

    # Delivery: Wednesday 5pm ET
    scheduler.add_job(run_delivery, "cron", day_of_week="wed", hour=17, minute=0)

    log.info("Funded & Found Out scheduler started.")
    log.info("  - Pipeline: Monday 9am ET")
    log.info("  - Delivery: Wednesday 5pm ET")
    scheduler.start()
