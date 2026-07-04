from mcp.base import MCPConnectorStatus, MCPDocument, MCPResource
from services.vector_store import load_mock_enterprise_documents


class LocalFilesMCPConnector:
    """MCP connector for local enterprise files (Excel, PDF, Gmail exports).

    Uses MCP resource URIs for local files until OAuth MCP servers are configured
    for Gmail and Google Drive.
    """

    server_id = "semanticshield-localfiles-mcp"
    source_name = "Local Files"
    transport = "file_system"
    connection_type = "mcp_local"

    SOURCE_MAP = {
        "Excel": ["excel"],
        "PDF": ["pdf"],
        "Gmail": ["gmail"],
        "Google Drive": ["google_drive"],
    }

    def list_resources(self) -> list[MCPResource]:
        return [
            MCPResource(uri="mcp://local/excel/sheets", name="Excel Sheets", description="Local Excel/CSV files"),
            MCPResource(uri="mcp://local/pdf/documents", name="PDF Documents", description="Local PDF/text files"),
            MCPResource(uri="mcp://local/gmail/exports", name="Gmail Exports", description="Local email export files"),
            MCPResource(uri="mcp://local/drive/files", name="Drive Files", description="Local drive export files"),
        ]

    async def fetch_documents(self) -> tuple[list[MCPDocument], MCPConnectorStatus]:
        raw_docs = load_mock_enterprise_documents()
        documents: list[MCPDocument] = []

        for doc in raw_docs:
            source = doc["source"]
            folder = next((k for k, v in self.SOURCE_MAP.items() if source.lower() in [x.lower() for x in v] or source == k), source)
            documents.append(
                MCPDocument(
                    source=source,
                    title=doc["title"],
                    content=doc["content"],
                    classification=doc.get("classification", "confidential"),
                    resource_uri=f"mcp://local/{source.lower().replace(' ', '_')}/{doc['title'].lower().replace(' ', '_')}",
                    connection_type=self.connection_type,
                )
            )

        status = MCPConnectorStatus(
            name="Local Files (Excel, PDF, Gmail, Drive)",
            server_id=self.server_id,
            transport=self.transport,
            connection_type=self.connection_type,
            status="connected" if documents else "disconnected",
            resource_count=len(documents),
            resources=self.list_resources(),
            last_error=None if documents else "No local files found in data/enterprise/",
        )
        return documents, status
