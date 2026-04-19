from base import Scraper, SearchConfig

from pydantic import Field
# from camoufox.async_api import AsyncCamoufox, launch_options
from playwright.async_api import BrowserType, async_playwright
import asyncio
import os
import typing
import httpx
from curl_cffi.requests import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from bs4 import BeautifulSoup
import re
from pydantic import BaseModel, Field


class MostaqlConfig(BaseModel):
    max_requests: int = 5
    requests_delay: float = 1.0
    
config = MostaqlConfig()

class MostaqlJob(BaseModel):
    title: str
    bids: str
    time_posted: str
    link: str
    id: str
    description: str
    status: str
    time_posted: str
    budget: str
    duration: str
    skills: list[str]
    client_name: str
    client_since: str
    hire_rate: str
    open_projects: str
    active_projects: str
    ongoing_conversations: str
    
def parse_mostaql_jobs(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for row in soup.select("tr.project-row"):
        title_tag = row.select_one(".card--title h2 a")
        if not title_tag:
            raise ValueError("Missing job title element (.card--title h2 a)")
        title = title_tag.get_text(strip=True)

        if not title_tag.has_attr("href"):
            raise ValueError(f"Missing href on title tag for job: {title!r}")
        link = title_tag["href"]

        time_tag = row.select_one("time")
        if not time_tag:
            raise ValueError(f"Missing <time> element for job: {title!r}")
        time_posted = time_tag.get_text(strip=True)

        bids_tag = row.select_one(".project__meta li:nth-of-type(3)")
        if not bids_tag:
            raise ValueError(f"Missing bids element (.project__meta li:nth-of-type(3)) for job: {title!r}")
        bids = bids_tag.text.strip()
        # <a href="https://mostaql.com/project/1229268-%D8%A5%D9%86%D8%AA%D8%A7%D8%AC-%D9%81%D9%8A%D8%AF%D9%8A%D9%88-%D9%8A%D8%AC%D8%B9%D9%84-%D8%A7%D9%84%D8%B5%D9%88%D8%B1%D8%A9-%D8%AA%D8%AA%D9%83%D9%84%D9%85" class="">إنتاج فيديو يجعل الصورة تتكلم</a>
        id = re.search(r"/project/(\d+)-", link)
        assert id, f"Could not extract job ID from link: {link}"
        jobs.append({
            'title': title,
            'bids': bids,
            'time_posted': time_posted,
            'link': link,
            'id': id.group(1),
        })

    return jobs


def parse_project(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # ── Description ──────────────────────────────────────────────────────────
    desc_tag = soup.select_one("#project-brief .carda__content")
    if not desc_tag:
        raise ValueError("Missing description element (#project-brief .carda__content)")
    description = desc_tag.get_text(separator="\n", strip=True)

    # ── Project meta ──────────────────────────────────────────────────────────
    meta = {}
    META_SELECTORS = {
    "status":    "#project-meta-panel .meta-row:nth-of-type(1) .meta-value",
    "posted_at": "#project-meta-panel .meta-row:nth-of-type(2) .meta-value",
    "budget":    "#project-meta-panel .meta-row:nth-of-type(3) .meta-value",
    "duration":  "#project-meta-panel .meta-row:nth-of-type(4) .meta-value",
}
    for key, selector in META_SELECTORS.items():
        tag = soup.select_one(selector)
        if not tag:
            raise ValueError(f"Missing meta element for '{key}' with selector: {selector}")
        meta[key] = tag.get_text(strip=True)
    
    status    = meta['status']
    posted_at = meta["posted_at"]
    budget    = meta["budget"]
    duration  = meta["duration"]

    # ── Skills ────────────────────────────────────────────────────────────────
    skills = [tag.get_text(strip=True) for tag in soup.select(".skills__item bdi")]
    if not skills:
        raise ValueError("No skills found (.skills__item bdi)")

    # ── Client info ───────────────────────────────────────────────────────────
    name_tag = soup.select_one(".profile__name bdi")
    if not name_tag:
        raise ValueError("Missing client name element (.profile__name bdi)")
    client_name = name_tag.get_text(strip=True)



    # ── Client stats ──────────────────────────────────────────────────────────
    CLIENT_STAT_SELECTORS = {
    "client_since":           ".table-meta tr:nth-of-type(1) td:nth-of-type(2)",
    "hire_rate":              ".table-meta tr:nth-of-type(2) td:nth-of-type(2)",
    "open_projects":          ".table-meta tr:nth-of-type(3) td:nth-of-type(2)",
    "active_projects":        ".table-meta tr:nth-of-type(4) td:nth-of-type(2)",
    "ongoing_conversations":  ".table-meta tr:nth-of-type(5) td:nth-of-type(2)",
}
    client_stats = {}
    for key, selector in CLIENT_STAT_SELECTORS.items():
        tag = soup.select_one(selector)
        if not tag:
            raise ValueError(f"Missing client stat element for '{key}' with selector: {selector}")
        client_stats[key] = tag.get_text(strip=True)

    return {
        "description": description,
        "status": status,
        "posted_at": posted_at,
        "budget": budget,
        "duration": duration,
        "skills": skills,
        "client_name": client_name,
        "client_since": client_stats["client_since"],
        "hire_rate": client_stats["hire_rate"],
        "open_projects": client_stats["open_projects"],
        "active_projects": client_stats["active_projects"],
        "ongoing_conversations": client_stats["ongoing_conversations"],
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(httpx.RequestError))
async def client_request(client, url: str, params: dict) -> dict:
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response

{
    "sort": "latest",
    "category": ["development", "ai-machine-learning"],
    "limit": 200
}
# TODO: add filters by time posted
class MostaqlSearchConfig(BaseModel):
    keyword: str = ""
    min_salary: int = 25
    max_salary: int = 10000
    sort: typing.Literal['latest', 'oldest', 'less_bids', 'more_bids'] = 'latest'
    category: typing.List[typing.Literal['business', 'development', 'ai-machine-learning', 'engineering-architecture', 'design', 'marketing', 'writing-translation', 'support', 'training']] = []
    limit: int = 20 
    
class MostaqlScraper(Scraper):
    name: str = "Mostaql"
    __base_url:str = "https://mostaql.com/projects"
    async def search(self, search_config: MostaqlSearchConfig) -> list[MostaqlJob]:
        global config
        
        client = AsyncSession(max_clients = config.max_requests)
        async with client:
            jobs = []
            for page in range(1, 1000):  # Arbitrary large number to paginate through results
                config_dict = self.resolve_config(page = page, config = search_config)
                response = await client_request(client, self.__base_url, config_dict)
                page_jobs = parse_mostaql_jobs(response.text)
                jobs_html = [client_request(client, job['link'], {}) for job in page_jobs]
                jobs_html = await asyncio.gather(*jobs_html)
                for job, html in zip(page_jobs, jobs_html):
                    details = parse_project(html.text)
                    job.update(details)
                print(f"Parsed {len(jobs)} jobs from Mostaql")
                jobs = jobs + [MostaqlJob(**job) for job in page_jobs]
                assert len(jobs) != 0, "No jobs found, something went wrong"
                if len(jobs) >= search_config.limit:
                    break
                
            return jobs
    
    def resolve_config(self, page: int, config: 'MostaqlSearchConfig') -> dict:
        config_dict = {
            "keyword": config.keyword,
            "budget_min": config.min_salary,
            "budget_max": config.max_salary,
            "sort": config.sort,
            "page": page
        }
        if config.category:
            config_dict["category"] = ",".join(config.category)
        return config_dict


async def main():
    scraper = MostaqlScraper()
    search_config = MostaqlSearchConfig(
        keyword="python web scraping",
        locations=["remote"],
        min_salary=25,
        max_salary=10000,
        limit=20

    )
    results = await scraper.search(search_config)
    print(f"Found {len(results)} jobs:")
    for job in results:
        print(f"- {job.title} (Bids: {job.bids}, Posted: {job.time_posted}, Link: {job.link})")
        print(f"  Description: {job.description}")

if __name__ == "__main__":
    asyncio.run(main())
