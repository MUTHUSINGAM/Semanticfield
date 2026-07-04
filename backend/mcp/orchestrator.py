from dataclasses import asdict
from typing import Any

from config import get_settings
from mcp.registry import get_all_connectors
from services.vector_store import load_mock_enterprise_documents


async def fetch_all_mcp_documents() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch documents from all MCP connectors.

    Returns (documents, connector_statuses)
    """
    settings = get_settings()
    all_documents: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []

    if settings.use_mock_enterprise_data:
        mock_docs = load_mock_enterprise_documents()
        for doc in mock_docs:
            all_documents.append({**doc, "connection_type": "mock", "resource_uri": f"mock://local/{doc['title']}"})
        statuses.append(
            {
                "name": "Mock Data",
                "server_id": "semanticshield-mock",
                "protocol": "none",
                "transport": "file_system",
                "connection_type": "mock",
                "status": "connected",
                "resource_count": len(mock_docs),
                "last_error": None,
                "resources": [],
            }
        )
        return all_documents, statuses

    for connector in get_all_connectors(include_local=True):
        docs, status = await connector.fetch_documents()
        statuses.append(_status_to_dict(status))
        for doc in docs:
            all_documents.append(
                {
                    "source": doc.source,
                    "title": doc.title,
                    "content": doc.content,
                    "classification": doc.classification,
                    "resource_uri": doc.resource_uri,
                    "connection_type": doc.connection_type,
                    "mcp_server_id": connector.server_id,
                }
            )

    return all_documents, statuses


async def get_mcp_status() -> list[dict[str, Any]]:
    settings = get_settings()
    if settings.use_mock_enterprise_data:
        return [
            {
                "name": source,
                "server_id": "semanticshield-mock",
                "protocol": "none",
                "transport": "file_system",
                "connection_type": "mock",
                "status": "connected",
                "resource_count": 0,
                "last_error": None,
                "resources": [{"uri": f"mock://local/{source.lower()}", "name": source, "description": "Mock file"}],
            }
            for source in ["Slack", "ClickUp", "Notion", "Gmail", "Google Drive", "Excel", "PDF"]
        ]

    statuses = []
    for connector in get_all_connectors(include_local=True):
        _, status = await connector.fetch_documents()
        statuses.append(_status_to_dict(status))
    return statuses


def _status_to_dict(status) -> dict[str, Any]:
    data = asdict(status)
    data["protocol"] = "mcp"
    data["resources"] = [asdict(r) for r in status.resources]
    return data
