import json
import logging
from datetime import datetime
from urllib.parse import quote_plus
import httpx
from sqlalchemy.orm import Session
from app.models import Company

logger = logging.getLogger(__name__)


def generate_research_links(name: str) -> dict:
    encoded = quote_plus(name)
    return {
        "glassdoor_url": f"https://www.glassdoor.com/Search/results.htm?keyword={encoded}",
        "levels_url": f"https://www.levels.fyi/companies/{encoded}/salaries/software-engineer",
        "blind_url": f"https://www.teamblind.com/search/{encoded}",
    }


def scrape_levels_fyi(name: str) -> str | None:
    encoded = quote_plus(name.lower().replace(" ", "-"))
    url = f"https://www.levels.fyi/companies/{encoded}/salaries/software-engineer"
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        if resp.status_code != 200:
            return None
        return json.dumps({"url": url, "status": "reachable"})
    except Exception as e:
        logger.warning(f"Levels.fyi scrape failed for {name}: {e}")
        return None


def research_company(company: Company, db: Session) -> Company:
    links = generate_research_links(company.name)
    company.glassdoor_url = links["glassdoor_url"]
    company.levels_url = links["levels_url"]
    company.blind_url = links["blind_url"]

    salary_data = scrape_levels_fyi(company.name)
    if salary_data:
        company.levels_salary_data = salary_data

    company.last_researched_at = datetime.utcnow()
    db.commit()
    db.refresh(company)
    return company
