"""SQLite tracker — prevents re-featuring companies and logs every run."""
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS covered_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    website_url TEXT,
                    funding_amount REAL,
                    run_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS run_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_date TEXT NOT NULL,
                    companies_found INTEGER DEFAULT 0,
                    companies_analyzed INTEGER DEFAULT 0,
                    pdf_path TEXT,
                    email_sent INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_recently_covered(self, company_name: str, weeks: int = 6) -> bool:
        """Return True if this company appeared in the last N weeks."""
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute(
                """SELECT COUNT(*) FROM covered_companies
                   WHERE LOWER(company_name) = LOWER(?)
                   AND date(run_date) >= date('now', ? || ' days')""",
                (company_name, f'-{weeks * 7}'),
            ).fetchone()[0]
        return count > 0

    def add_covered_companies(self, companies: list[dict], run_date: str):
        with sqlite3.connect(self.db_path) as conn:
            for c in companies:
                conn.execute(
                    """INSERT INTO covered_companies
                       (company_name, website_url, funding_amount, run_date)
                       VALUES (?, ?, ?, ?)""",
                    (
                        c.get('company_name', ''),
                        c.get('website_url', ''),
                        c.get('funding_amount'),
                        run_date,
                    ),
                )
            conn.commit()

    def get_latest_company_names(self) -> list[str]:
        """Return company names from the most recent run."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT run_date FROM run_history ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if not row:
                return []
            rows = conn.execute(
                "SELECT company_name FROM covered_companies WHERE run_date = ? ORDER BY id",
                (row[0],),
            ).fetchall()
            return [r[0] for r in rows]

    def log_run(
        self,
        run_date: str,
        companies_found: int,
        companies_analyzed: int,
        pdf_path: str = None,
        email_sent: bool = False,
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO run_history
                   (run_date, companies_found, companies_analyzed, pdf_path, email_sent)
                   VALUES (?, ?, ?, ?, ?)""",
                (run_date, companies_found, companies_analyzed, pdf_path, 1 if email_sent else 0),
            )
            conn.commit()
