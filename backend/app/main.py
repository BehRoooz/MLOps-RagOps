from fastapi import FastAPI
from app.core.config import settings
from app.api import health, ingest, search, chat, stats, embeddings, pdf, batch_ingest, search_rerank

# Prometheus instrumentation
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# Mount routers
app.include_router(health.router, tags=["health"])
app.include_router(ingest.router, tags=["ingest"])
app.include_router(search.router, tags=["search"])
app.include_router(chat.router, tags=["chat"])
app.include_router(stats.router, tags=["stats"])
app.include_router(embeddings.router, tags=["embeddings"])
app.include_router(pdf.router, tags=["pdf"])
app.include_router(batch_ingest.router, tags=["batch_ingest"])
app.include_router(search_rerank.router, prefix="", tags=["search"])


# Prometheus instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=False,
    should_respect_env_var=False,
)
instrumentator.instrument(app).expose(app, include_in_schema=False, should_gzip=False)
