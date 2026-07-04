from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from config import get_settings
from database import get_db
from mcp.orchestrator import fetch_all_mcp_documents, get_mcp_status
from models.schemas import EnterpriseSource, UserRole
from services.auth import require_roles
from services.mcp_sync import get_sync_status, run_mcp_sync
from services.slack_setup import verify_slack_connection

router = APIRouter(prefix="/api/sources", tags=["sources"])

SOURCE_TYPES = {
    "Slack": "messaging",
    "ClickUp": "project_management",
    "Notion": "wiki",
    "Gmail": "email",
    "Google Drive": "storage",
    "Excel": "spreadsheet",
    "PDF": "documents",
}


@router.get("", response_model=list[EnterpriseSource])
async def list_sources(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER, UserRole.AUDITOR))):
    db = get_db()
    settings = get_settings()
    cursor = db.enterprise_sources.find()
    sources: list[EnterpriseSource] = []
    async for doc in cursor:
        sources.append(_doc_to_source(doc))

    if not sources:
        mcp_statuses = await get_mcp_status()
        for status in mcp_statuses:
            if status["name"] == "Local Files (Excel, PDF, Gmail, Drive)":
                for local_name in ["Excel", "PDF", "Gmail", "Google Drive"]:
                    sources.append(
                        EnterpriseSource(
                            name=local_name,
                            type=SOURCE_TYPES.get(local_name, "documents"),
                            status="connected" if not settings.use_mock_enterprise_data else "connected",
                            document_count=0,
                            connection_type="mcp_local" if not settings.use_mock_enterprise_data else "mock",
                            mcp_server_id=status["server_id"],
                            protocol=status.get("protocol", "mcp"),
                        )
                    )
            else:
                sources.append(
                    EnterpriseSource(
                        name=status["name"],
                        type=SOURCE_TYPES.get(status["name"], "integration"),
                        status=status["status"],
                        document_count=status.get("resource_count", 0),
                        connection_type=status.get("connection_type", "mcp_live"),
                        mcp_server_id=status.get("server_id"),
                        protocol=status.get("protocol", "mcp"),
                        resource_uri=status["resources"][0]["uri"] if status.get("resources") else None,
                        last_error=status.get("last_error"),
                    )
                )
    return sources


@router.get("/mcp-status")
async def mcp_status(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER, UserRole.AUDITOR))):
    settings = get_settings()
    statuses = await get_mcp_status()
    return {
        "mode": "mock" if settings.use_mock_enterprise_data else "mcp_live",
        "protocol": "Model Context Protocol (MCP)",
        "description": "Each connector exposes MCP Resources (mcp://...) that SemanticShield reads and indexes into LanceDB.",
        "connectors": statuses,
    }


@router.get("/sync-status")
async def sync_status(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER, UserRole.AUDITOR))):
    return await get_sync_status()


@router.get("/slack/verify")
async def slack_verify(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER))):
    return await verify_slack_connection()


@router.post("/ingest")
async def ingest_enterprise_data(_user=Depends(require_roles(UserRole.ADMIN))):
    return await run_mcp_sync(trigger="manual")


def _doc_to_source(doc: dict) -> EnterpriseSource:
    return EnterpriseSource(
        name=doc["name"],
        type=doc["type"],
        status=doc["status"],
        document_count=doc.get("document_count", 0),
        last_synced=doc.get("last_synced"),
        connection_type=doc.get("connection_type", "mock"),
        mcp_server_id=doc.get("mcp_server_id"),
        protocol=doc.get("protocol", "none"),
        resource_uri=doc.get("resource_uri"),
        last_error=doc.get("last_error"),
    )
