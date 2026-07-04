import httpx

from config import get_settings
from mcp.base import MCPConnectorStatus, MCPDocument, MCPResource


class ClickUpMCPConnector:
    """MCP connector for ClickUp — server_id: semanticshield-clickup-mcp"""

    server_id = "semanticshield-clickup-mcp"
    source_name = "ClickUp"
    transport = "https_api"
    connection_type = "mcp_live"

    def list_resources(self) -> list[MCPResource]:
        return [
            MCPResource(
                uri="mcp://clickup/tasks",
                name="Workspace Tasks",
                description="Tasks and descriptions from ClickUp workspace",
            ),
            MCPResource(
                uri="mcp://clickup/lists",
                name="Lists",
                description="ClickUp lists in workspace",
            ),
        ]

    async def fetch_documents(self) -> tuple[list[MCPDocument], MCPConnectorStatus]:
        settings = get_settings()
        token = settings.clickup_api_token.strip()
        workspace_id = settings.clickup_workspace_id.strip()
        status = MCPConnectorStatus(
            name=self.source_name,
            server_id=self.server_id,
            transport=self.transport,
            connection_type=self.connection_type,
            resources=self.list_resources(),
        )

        if not token or not workspace_id:
            status.status = "disconnected"
            status.last_error = "CLICKUP_API_TOKEN or CLICKUP_WORKSPACE_ID not configured"
            return [], status

        headers = {"Authorization": token}
        documents: list[MCPDocument] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                teams_resp = await client.get("https://api.clickup.com/api/v2/team", headers=headers)
                teams_resp.raise_for_status()

                tasks_resp = await client.get(
                    f"https://api.clickup.com/api/v2/team/{workspace_id}/task",
                    headers=headers,
                    params={"page": 0, "include_closed": False, "subtasks": True},
                )
                tasks_data = tasks_resp.json()
                if tasks_resp.status_code != 200:
                    status.status = "error"
                    status.last_error = tasks_data.get("err", f"HTTP {tasks_resp.status_code}")
                    return [], status

                for task in tasks_data.get("tasks", [])[:30]:
                    name = task.get("name", "Untitled Task")
                    description = task.get("description") or task.get("text_content") or ""
                    status_name = task.get("status", {}).get("status", "")
                    content = f"ClickUp Task: {name}\nStatus: {status_name}\n{description}".strip()
                    if len(content) < 20:
                        continue

                    classification = "highly_confidential" if any(
                        w in name.lower() + description.lower()
                        for w in ("roadmap", "confidential", "salary", "release")
                    ) else "confidential"

                    documents.append(
                        MCPDocument(
                            source=self.source_name,
                            title=name,
                            content=content,
                            classification=classification,
                            resource_uri=f"mcp://clickup/tasks/{task.get('id', '')}",
                            connection_type=self.connection_type,
                            metadata={"task_id": task.get("id"), "status": status_name},
                        )
                    )

            status.status = "connected"
            status.resource_count = len(documents)
            return documents, status

        except Exception as exc:
            status.status = "error"
            status.last_error = str(exc)
            return documents, status
