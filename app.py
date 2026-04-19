import os

from fastapi import FastAPI, Depends
import uvicorn
from mostaql import MostaqlConfig, MostaqlJob, MostaqlScraper, MostaqlSearchConfig
import asyncio
from typing import Annotated
import json

app = FastAPI()
port = 8000
host = "127.0.0.1"

jobs_file = "mostaql_jobs.json"

class Job(MostaqlJob):
    is_user_notified: bool = False

# class MostaqlSearchConfig(BaseModel):
#     keyword: str = ""
#     min_salary: int = 25
#     max_salary: int = 10000
#     sort: typing.Literal['latest', 'oldest', 'less_bids', 'more_bids'] = 'latest'
#     category: typing.List[typing.Literal['business', 'development', 'ai-machine-learning', 'engineering-architecture', 'design', 'marketing', 'writing-translation', 'support', 'training']] = []
#     limit: int = 20 



@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/search", response_model=list[MostaqlJob])
async def scrape_jobs(search_config: Annotated[MostaqlSearchConfig, Depends()]) -> list[MostaqlJob]:
# async def scrape_jobs(search_config: MostaqlSearchConfig ) -> list[MostaqlJob]:
    scraper = MostaqlScraper()
    results = await scraper.search(search_config)
    if not os.path.exists(jobs_file):
        with open(jobs_file, "w") as f:
            json.dump([], f)

    with open(jobs_file, "r") as f:
        existing_jobs = json.load(f)
    new_jobs_dict = existing_jobs + [job.model_dump(mode='json') for job in results]
    
    with open(jobs_file, "w") as f:
        json.dump(new_jobs_dict, f, indent=4)

    return results

# @app.get("/search", response_model=list[Job])
# async def search_jobs(search_config: Annotated[MostaqlSearchConfig, Depends()]) -> list[MostaqlJob]:
#     """same as scrape but modify the output to be bot suitable"""
#     scraper = MostaqlScraper()
#     results = await scraper.search(search_config)
#     results = [Job(**job.model_dump()) for job in results]
#     return results


# @app.get("/register")
# async def register(ids: list[int]):
#     if not os.path.exists(jobs_file):
#         with open(jobs_file, "w") as f:
#             json.dump({}, f)
        
#     with open(jobs_file, "r") as f:
#         existing_jobs = json.load(f)
#     not_found_ids = [job_id for job_id in ids if job_id not in existing_jobs.keys()]
#     assert len(not_found_ids) == 0, f"Some job ids were not found make sure this ids exist: {not_found_ids}"
#     for job_id in ids:
#         existing_jobs[job_id]["registered"] = True
#     with open(jobs_file, "w") as f:
#         json.dump(existing_jobs, f, indent=4)
#     return "Jobs registered successfully"



if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port)
