"""Central MCP sync service — used by manual ingest, scheduler, and Slack realtime."""
from datetime import datetime, timezone
from typing import Any

from config import get_settings
from database import get_db
from mcp.orchestrator import fetch_all_mcp_documents
from services.vector_store import vector_store

SOURCE_TYPES = {
    "Slack": "messaging",
    "ClickUp": "project_management",
    "Notion": "wiki",
    "Gmail": "email",
    "Google Drive": "storage",
    "Excel": "spreadsheet",
    "PDF": "documents",
}

_sync_lock = False


async def run_mcp_sync(trigger: str = "manual") -> dict[str, Any]:
    global _sync_lock
    if _sync_lock:
        return {"status": "skipped", "reason": "sync already in progress"}

    _sync_lock = True
    settings = get_settings()
    db = get_db()
    started = datetime.now(timezone.utc)

    try:
        await db.sync_state.update_one(
            {"_id": "mcp_sync"},
            {"$set": {"status": "running", "trigger": trigger, "started_at": started.isoformat()}},
            upsert=True,
        )

        documents, mcp_statuses = await fetch_all_mcp_documents()
        chunks = await vector_store.ingest_documents(documents)
        now = datetime.now(timezone.utc).isoformat()

        source_counts: dict[str, int] = {}
        for doc in documents:
            source_counts[doc["source"]] = source_counts.get(doc["source"], 0) + 1

        for status in mcp_statuses:
            name = status["name"]
            if name.startswith("Local Files"):
                for local_name in ["Excel", "PDF", "Gmail", "Google Drive"]:
                    await _upsert_source(db, local_name, status, source_counts, now)
            else:
                await _upsert_source(db, name, status, source_counts, now)

        result = {
            "status": "success",
            "trigger": trigger,
            "mode": "mock" if settings.use_mock_enterprise_data else "mcp_live",
            "documents_ingested": len(documents),
            "chunks_indexed": chunks,
            "mcp_connectors": mcp_statuses,
            "synced_at": now,
        }

        await db.sync_state.update_one(
            {"_id": "mcp_sync"},
            {
                "$set": {
                    "status": "idle",
                    "last_sync_at": now,
                    "last_trigger": trigger,
                    "last_result": {
                        "documents": len(documents),
                        "chunks": chunks,
                    },
                    "realtime_enabled": settings.mcp_realtime_sync_enabled,
                    "interval_seconds": settings.mcp_sync_interval_seconds,
                }
            },
            upsert=True,
        )
        return result

    except Exception as exc:
        await db.sync_state.update_one(
            {"_id": "mcp_sync"},
            {"$set": {"status": "error", "last_error": str(exc), "last_trigger": trigger}},
            upsert=True,
        )
        raise
    finally:
        _sync_lock = False


async def get_sync_status() -> dict[str, Any]:
    db = get_db()
    settings = get_settings()
    doc = await db.sync_state.find_one({"_id": "mcp_sync"})
    return {
        "realtime_enabled": settings.mcp_realtime_sync_enabled,
        "interval_seconds": settings.mcp_sync_interval_seconds,
        "slack_socket_mode": bool(settings.slack_app_token and settings.slack_bot_token),
        "status": doc.get("status", "idle") if doc else "idle",
        "last_sync_at": doc.get("last_sync_at") if doc else None,
        "last_trigger": doc.get("last_trigger") if doc else None,
        "last_result": doc.get("last_result") if doc else None,
        "last_error": doc.get("last_error") if doc else None,
    }


async def _upsert_source(db, name: str, status: dict, source_counts: dict, now: str) -> None:
    await db.enterprise_sources.update_one(
        {"name": name},
        {
            "$set": {
                "name": name,
                "type": SOURCE_TYPES.get(name, "integration"),
                "status": status["status"],
                "document_count": source_counts.get(name, status.get("resource_count", 0)),
                "last_synced": now,
                "connection_type": status.get("connection_type", "mcp_live"),
                "mcp_server_id": status.get("server_id"),
                "protocol": status.get("protocol", "mcp"),
                "last_error": status.get("last_error"),
            }
        },
        upsert=True,
    )
