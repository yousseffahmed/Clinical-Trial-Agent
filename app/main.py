"""FastAPI entry point for the Clinical Trial Assistant."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .agent import clinical_agent
from .config import settings
from .logger import configure_logging, get_logger
from .memory import clear_memories, init_db, list_memories, save_memory
from .rag import ingest_documents, rag_service
from .schemas import ChatRequest, ChatResponse, IngestResponse, MemoryCreate
from .tools import list_capabilities

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info(
        "Application started in %s mode; RAG index ready=%s; LLM enabled=%s",
        settings.app_env,
        rag_service.is_ingested(),
        settings.llm_enabled,
    )
    yield


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="Grounded clinical-trial document Q&A, risk, planning, and memory.",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "project": settings.project_name,
        "status": "running",
        "mode": "llm" if settings.llm_enabled else "mock",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "rag_ready": rag_service.is_ingested(),
        "llm_enabled": settings.llm_enabled,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return clinical_agent.run(
            request.message, use_memory=request.use_memory, debug=request.debug
        )
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest", response_model=IngestResponse)
def ingest():
    try:
        result = ingest_documents()
        return result
    except Exception as exc:
        logger.exception("Document ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/memory")
def get_memory():
    return {"memories": list_memories()}


@app.post("/memory", status_code=201)
def create_memory(request: MemoryCreate):
    try:
        return {"status": "saved", "memory": save_memory(request.key, request.value)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/memory")
def delete_memory():
    return {"status": "cleared", "deleted": clear_memories()}


@app.get("/tools")
def tools():
    return list_capabilities()
