from mcp.base import MCPConnector
from mcp.connectors.clickup_connector import ClickUpMCPConnector
from mcp.connectors.local_files_connector import LocalFilesMCPConnector
from mcp.connectors.notion_connector import NotionMCPConnector
from mcp.connectors.slack_connector import SlackMCPConnector

LIVE_MCP_CONNECTORS: list[MCPConnector] = [
    SlackMCPConnector(),
    ClickUpMCPConnector(),
    NotionMCPConnector(),
]

LOCAL_MCP_CONNECTORS: list[MCPConnector] = [
    LocalFilesMCPConnector(),
]


def get_all_connectors(include_local: bool = True) -> list[MCPConnector]:
    connectors: list[MCPConnector] = list(LIVE_MCP_CONNECTORS)
    if include_local:
        connectors.extend(LOCAL_MCP_CONNECTORS)
    return connectors
