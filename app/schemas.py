"""Pydantic request and response contracts for the public API."""

from typing import List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    use_memory: bool = True
    debug: bool = False


class ChatResponse(BaseModel):
    answer: str
    plan_summary: str = ""
    tools_used: List[str] = Field(default_factory=list)
    retrieved_sources: List[str] = Field(default_factory=list)
    memory_used: List[str] = Field(default_factory=list)


class MemoryCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=2_000)


class MemoryRecord(BaseModel):
    id: int
    key: str
    value: str
    created_at: str


class IngestResponse(BaseModel):
    status: str
    documents: int
    chunks: int
    embedding_backend: str
    sources: List[str]
