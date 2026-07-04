"""MCP (Model Context Protocol) connector base types.

An MCP connector exposes enterprise data as MCP Resources with URIs like:
  mcp://slack/channels/messages
  mcp://clickup/tasks
  mcp://notion/pages

SemanticShield acts as an MCP *client* — it reads resources from MCP servers/connectors
and ingests them into LanceDB for DLP semantic search.
"""
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class MCPResource:
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


@dataclass
class MCPDocument:
    source: str
    title: str
    content: str
    classification: str = "confidential"
    resource_uri: str = ""
    connection_type: str = "mcp_live"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPConnectorStatus:
    name: str
    server_id: str
    protocol: str = "mcp"
    transport: str = "embedded"
    connection_type: str = "mcp_live"
    status: str = "disconnected"
    resource_count: int = 0
    last_error: str | None = None
    resources: list[MCPResource] = field(default_factory=list)


class MCPConnector(Protocol):
    """Every enterprise app connector must implement this MCP interface."""

    server_id: str
    source_name: str
    transport: str
    connection_type: str

    def list_resources(self) -> list[MCPResource]: ...

    async def fetch_documents(self) -> tuple[list[MCPDocument], MCPConnectorStatus]: ...
