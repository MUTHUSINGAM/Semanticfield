import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import get_db
from routers import audit, auth, chat, dashboard, sources
from services.mcp_sync import run_mcp_sync
from services.sync_scheduler import start_background_sync, stop_background_sync
from services.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = get_db()

    table_exists = settings.lancedb_table_name in vector_store.db.table_names()
    if not table_exists:
        try:
            await run_mcp_sync(trigger="startup")
        except Exception:
            pass

    await start_background_sync()

    yield

    await stop_background_sync()


app = FastAPI(title="SemanticShield AI", version="1.0.0", lifespan=lifespan)

settings = get_settings()
cors_kwargs = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.app_env == "development":
    cors_kwargs["allow_origin_regex"] = r"http://localhost:\d+"
else:
    cors_kwargs["allow_origins"] = settings.cors_origin_list

app.add_middleware(CORSMiddleware, **cors_kwargs)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(audit.router)
app.include_router(sources.router)


@app.get("/api/health")
async def health():
    from services.mcp_sync import get_sync_status

    sync = await get_sync_status()
    return {
        "status": "ok",
        "app": settings.app_name,
        "enterprise": settings.enterprise_name,
        "demo_mode": settings.demo_mode,
        "mcp_sync": sync,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
