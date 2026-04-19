# Mostaql JobSearch Automation

A project for scraping job listings from the Mostaql freelancing platform and exposing results through a simple FastAPI endpoint allowing interactoin between llms and the scraper through N8N

## Overview

This repository includes a job scraper and API wrapper for Mostaql. It fetches project listings, parses job details and client information, and saves results to a JSON file.

## Key Components

- `app.py`
  - FastAPI application with a `/search` endpoint.
  - Uses `MostaqlScraper` to perform searches and persist results to `mostaql_jobs.json`.

- `mostaql.py`
  - Contains search configuration models, scraping logic, and HTML parsers.
  - Extracts job metadata, description, skills, client profile, and project details.

- `base.py`
  - Defines generic scraper base classes and shared search models.

- `mostaql_jobs.json`
  - Output file where scraped job results are appended.

## Features

- Search Mostaql projects by keyword, budget range, category, sort order, and result limit.
- Parse detailed project information including:
  - title, bids, posting time, description, budget, duration
  - skills, client name, hire rate, open projects, active projects, ongoing conversations
- Store search results locally in JSON format.

## Usage

1. Install dependencies:

```powershell
pip install fastapi uvicorn pydantic httpx curl_cffi tenacity beautifulsoup4 playwright
```

2. Run the API server:

```powershell
python app.py
```

3. Perform a job search by opening a browser or using `curl`:

```powershell
curl "http://127.0.0.1:8000/search?keyword=python&min_salary=25&max_salary=10000&sort=latest&limit=20"
```

## Search Parameters

The `/search` endpoint accepts the following query parameters:

- `keyword` (string): Search keyword for project titles and descriptions.
- `min_salary` (int): Minimum budget filter.
- `max_salary` (int): Maximum budget filter.
- `sort` (string): Sort order (`latest`, `oldest`, `less_bids`, `more_bids`).
- `category` (list): One or more categories from:
  - `business`, `development`, `ai-machine-learning`, `engineering-architecture`, `design`, `marketing`, `writing-translation`, `support`, `training`
- `limit` (int): Maximum number of jobs to return.

## Output

Search results are returned as JSON and also saved to `mostaql_jobs.json`.

## Notes

- The project is designed for Mostaql scraping and assumes the target HTML structure matches the parser selectors.
- Some endpoints and features are commented out and available for future extension.

## License

Use and modify this project freely.
