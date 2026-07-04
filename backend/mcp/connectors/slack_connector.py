import httpx

from config import get_settings
from mcp.base import MCPConnectorStatus, MCPDocument, MCPResource


class SlackMCPConnector:
    """MCP connector for Slack — server_id: semanticshield-slack-mcp"""

    server_id = "semanticshield-slack-mcp"
    source_name = "Slack"
    transport = "https_api"
    connection_type = "mcp_live"

    def list_resources(self) -> list[MCPResource]:
        return [
            MCPResource(
                uri="mcp://slack/channels/messages",
                name="Channel Messages",
                description="Recent messages from Slack channels the bot can access",
            ),
            MCPResource(
                uri="mcp://slack/channels/list",
                name="Channel List",
                description="List of Slack channels",
            ),
        ]

    async def fetch_documents(self) -> tuple[list[MCPDocument], MCPConnectorStatus]:
        settings = get_settings()
        token = settings.slack_bot_token.strip()
        status = MCPConnectorStatus(
            name=self.source_name,
            server_id=self.server_id,
            transport=self.transport,
            connection_type=self.connection_type,
            resources=self.list_resources(),
        )

        if not token:
            status.status = "disconnected"
            status.last_error = "SLACK_BOT_TOKEN not configured"
            return [], status

        headers = {"Authorization": f"Bearer {token}"}
        documents: list[MCPDocument] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                channels_resp = await client.get(
                    "https://slack.com/api/conversations.list",
                    headers=headers,
                    params={"types": "public_channel,private_channel", "limit": 20},
                )
                channels_data = channels_resp.json()
                if not channels_data.get("ok"):
                    status.status = "error"
                    err = channels_data.get("error", "Slack API error")
                    if err == "missing_scope":
                        status.last_error = (
                            "Slack bot missing scopes. Add: channels:history, channels:read, "
                            "groups:history, groups:read — then reinstall app to workspace."
                        )
                    else:
                        status.last_error = err
                    return [], status

                for channel in channels_data.get("channels", [])[:10]:
                    channel_id = channel["id"]
                    channel_name = channel.get("name", channel_id)
                    history_resp = await client.get(
                        "https://slack.com/api/conversations.history",
                        headers=headers,
                        params={"channel": channel_id, "limit": 15},
                    )
                    history = history_resp.json()
                    if not history.get("ok"):
                        continue

                    messages = []
                    for msg in history.get("messages", []):
                        text = msg.get("text", "").strip()
                        if text and not msg.get("subtype"):
                            messages.append(text)

                    if messages:
                        content = f"Slack Channel #{channel_name}\n" + "\n".join(messages)
                        documents.append(
                            MCPDocument(
                                source=self.source_name,
                                title=f"Channel #{channel_name}",
                                content=content,
                                classification="confidential",
                                resource_uri=f"mcp://slack/channels/{channel_id}/messages",
                                connection_type=self.connection_type,
                                metadata={"channel_id": channel_id, "channel_name": channel_name},
                            )
                        )

            status.status = "connected"
            status.resource_count = len(documents)
            return documents, status

        except Exception as exc:
            status.status = "error"
            status.last_error = str(exc)
            return documents, status
