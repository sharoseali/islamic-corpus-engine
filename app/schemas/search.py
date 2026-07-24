"""Search API response schemas."""

from pydantic import BaseModel


class SearchHitOut(BaseModel):
    doc_type: str
    language_code: str
    collection_key: str
    citation: str
    source_row_id: int
    text: str
    score: float
    match: str
    ref: dict = {}


class SearchResponseOut(BaseModel):
    query: str
    language_code: str
    total: int
    hits: list[SearchHitOut] = []
