import httpx

from config import get_settings
from mcp.base import MCPConnectorStatus, MCPDocument, MCPResource


class NotionMCPConnector:
    """MCP connector for Notion — server_id: semanticshield-notion-mcp"""

    server_id = "semanticshield-notion-mcp"
    source_name = "Notion"
    transport = "https_api"
    connection_type = "mcp_live"

    def list_resources(self) -> list[MCPResource]:
        return [
            MCPResource(
                uri="mcp://notion/pages",
                name="Notion Pages",
                description="Pages and databases from Notion workspace",
            ),
            MCPResource(
                uri="mcp://notion/databases",
                name="Notion Databases",
                description="Database entries from Notion",
            ),
        ]

    async def fetch_documents(self) -> tuple[list[MCPDocument], MCPConnectorStatus]:
        settings = get_settings()
        token = settings.notion_api_key.strip()
        database_id = settings.notion_database_id.strip()
        status = MCPConnectorStatus(
            name=self.source_name,
            server_id=self.server_id,
            transport=self.transport,
            connection_type=self.connection_type,
            resources=self.list_resources(),
        )

        if not token:
            status.status = "disconnected"
            status.last_error = "NOTION_API_KEY not configured"
            return [], status

        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        documents: list[MCPDocument] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if database_id:
                    db_resp = await client.post(
                        f"https://api.notion.com/v1/databases/{database_id}/query",
                        headers=headers,
                        json={"page_size": 25},
                    )
                    if db_resp.status_code == 200:
                        for page in db_resp.json().get("results", []):
                            doc = _notion_page_to_document(page, self.source_name, self.connection_type)
                            if doc:
                                documents.append(doc)

                search_resp = await client.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json={"page_size": 20, "filter": {"value": "page", "property": "object"}},
                )
                if search_resp.status_code == 200:
                    for page in search_resp.json().get("results", []):
                        page_id = page.get("id", "")
                        if any(d.resource_uri == f"mcp://notion/pages/{page_id}" for d in documents):
                            continue
                        blocks_resp = await client.get(
                            f"https://api.notion.com/v1/blocks/{page_id}/children",
                            headers=headers,
                            params={"page_size": 50},
                        )
                        if blocks_resp.status_code == 200:
                            page_with_blocks = {**page, "_blocks": blocks_resp.json().get("results", [])}
                            doc = _notion_page_to_document(page_with_blocks, self.source_name, self.connection_type)
                            if doc:
                                documents.append(doc)

            if not documents:
                status.status = "connected"
                status.last_error = (
                    "Connected but no pages returned. Share Notion pages/databases with your integration."
                )
            else:
                status.status = "connected"
            status.resource_count = len(documents)
            return documents, status

        except Exception as exc:
            status.status = "error"
            status.last_error = str(exc)
            return documents, status


def _notion_page_to_document(page: dict, source_name: str, connection_type: str) -> MCPDocument | None:
    props = page.get("properties", {})
    title = "Untitled"
    for prop in props.values():
        if prop.get("type") == "title":
            parts = prop.get("title", [])
            title = "".join(p.get("plain_text", "") for p in parts) or "Untitled"
            break

    content_parts = [f"Notion Page: {title}"]
    for block in page.get("_blocks", []):
        text = _extract_block_text(block)
        if text:
            content_parts.append(text)

    content = "\n".join(content_parts)
    if len(content) < 15:
        return None

    page_id = page.get("id", "")
    classification = "highly_confidential" if any(
        w in content.lower() for w in ("confidential", "policy", "salary", "internal only")
    ) else "confidential"

    return MCPDocument(
        source=source_name,
        title=title,
        content=content,
        classification=classification,
        resource_uri=f"mcp://notion/pages/{page_id}",
        connection_type=connection_type,
        metadata={"page_id": page_id},
    )


def _extract_block_text(block: dict) -> str:
    block_type = block.get("type", "")
    data = block.get(block_type, {})
    if "rich_text" in data:
        return "".join(t.get("plain_text", "") for t in data["rich_text"])
    if block_type == "code":
        return data.get("rich_text", [{}])[0].get("plain_text", "") if data.get("rich_text") else ""
    return ""
