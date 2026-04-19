from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

import pydantic
import typing
import os
import time
import json

import asyncio

class Job(BaseModel):
    title: str
    company: str
    description: str
    url: str
    
class Scraper(BaseModel):
    name: str

    @abstractmethod
    async def search(self, query: str, config: 'SearchConfig') -> 'SearchResult':
        raise NotImplementedError("Subclasses must implement the search method.")
    def resolve_config(self, config: 'SearchConfig') -> dict:
        return config.dict()

class SearchConfig(BaseModel):
    locations: typing.List[str] = Field(default_factory=list)
    min_salary: int = 0
    max_salary: int = 0
    job_type: typing.Literal['full-time', 'part-time', 'contract', 'internship', 'one_time'] = 'full-time'
    remote: bool = False

class SearchResult(BaseModel):
    jobs: typing.List[Job] = Field(default_factory=list)


class Config(BaseModel):
    pass
