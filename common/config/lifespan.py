from contextlib import asynccontextmanager

from fastapi import FastAPI

from langchain.vector_store import refresh_documents_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    refresh_documents_scheduler.start_scheduler()
    yield
    # shutdown
