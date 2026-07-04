"""Slack connection diagnostics and setup guidance."""
import httpx

from config import get_settings

REQUIRED_BOT_SCOPES = [
    "channels:history",
    "channels:read",
    "groups:history",
    "groups:read",
    "im:history",
    "im:read",
    "mpim:history",
    "mpim:read",
]

REQUIRED_EVENT_SUBSCRIPTIONS = [
    "message.channels",
    "message.groups",
    "message.im",
]

SOCKET_MODE_APP_SCOPE = "connections:write"


async def verify_slack_connection() -> dict:
    settings = get_settings()
    bot_token = settings.slack_bot_token.strip()
    app_token = settings.slack_app_token.strip()

    result = {
        "bot_token_configured": bool(bot_token),
        "app_token_configured": bool(app_token),
        "bot_auth_ok": False,
        "can_list_channels": False,
        "can_read_history": False,
        "socket_mode_ready": bool(app_token.startswith("xapp-")),
        "missing_scopes": [],
        "setup_steps": [],
        "errors": [],
    }

    if not bot_token:
        result["errors"].append("SLACK_BOT_TOKEN is missing in .env")
        result["setup_steps"] = _setup_steps()
        return result

    headers = {"Authorization": f"Bearer {bot_token}"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        auth_resp = await client.get("https://slack.com/api/auth.test", headers=headers)
        auth_data = auth_resp.json()
        if auth_data.get("ok"):
            result["bot_auth_ok"] = True
            result["team"] = auth_data.get("team")
            result["bot_user"] = auth_data.get("user")
        else:
            result["errors"].append(f"auth.test failed: {auth_data.get('error')}")
            result["setup_steps"] = _setup_steps()
            return result

        scopes_resp = await client.get(
            "https://slack.com/api/auth.scopes.list",
            headers=headers,
        )
        if scopes_resp.status_code == 200:
            scopes_data = scopes_resp.json()
            if scopes_data.get("ok"):
                granted = set(scopes_data.get("info", {}).get("bot", []))
                missing = [s for s in REQUIRED_BOT_SCOPES if s not in granted]
                result["granted_scopes"] = sorted(granted)
                result["missing_scopes"] = missing
            else:
                result["missing_scopes"] = REQUIRED_BOT_SCOPES
                result["errors"].append("Could not list scopes — verify manually in Slack app settings")

        list_resp = await client.get(
            "https://slack.com/api/conversations.list",
            headers=headers,
            params={"types": "public_channel,private_channel", "limit": 5},
        )
        list_data = list_resp.json()
        if list_data.get("ok"):
            result["can_list_channels"] = True
            channels = list_data.get("channels", [])
            if channels:
                hist_resp = await client.get(
                    "https://slack.com/api/conversations.history",
                    headers=headers,
                    params={"channel": channels[0]["id"], "limit": 1},
                )
                hist_data = hist_resp.json()
                if hist_data.get("ok"):
                    result["can_read_history"] = True
                else:
                    err = hist_data.get("error", "")
                    result["errors"].append(f"Cannot read channel history: {err}")
                    if err == "missing_scope" and "channels:history" not in result["missing_scopes"]:
                        result["missing_scopes"].append("channels:history")
        else:
            err = list_data.get("error", "")
            result["errors"].append(f"conversations.list failed: {err}")
            if err == "missing_scope":
                result["missing_scopes"] = list(set(result["missing_scopes"] + REQUIRED_BOT_SCOPES))

    if result["missing_scopes"]:
        result["setup_steps"] = _setup_steps(result["missing_scopes"])

    result["status"] = (
        "connected"
        if result["can_list_channels"] and result["can_read_history"]
        else "needs_setup"
        if result["bot_auth_ok"]
        else "error"
    )
    return result


def _setup_steps(missing: list[str] | None = None) -> list[str]:
    steps = [
        "1. Go to https://api.slack.com/apps → select your SemanticShield app",
        "2. OAuth & Permissions → Bot Token Scopes → Add: "
        + ", ".join(missing or REQUIRED_BOT_SCOPES),
        "3. Click 'Reinstall to Workspace' at the top of OAuth & Permissions",
        "4. In Slack, invite the bot: /invite @YourBotName in each channel to monitor",
        "5. For REALTIME sync: Settings → Socket Mode → Enable → generate App-Level Token with connections:write",
        "6. Event Subscriptions → Enable → Subscribe to bot events: "
        + ", ".join(REQUIRED_EVENT_SUBSCRIPTIONS),
        "7. Put SLACK_BOT_TOKEN (xoxb-...) and SLACK_APP_TOKEN (xapp-...) in .env → restart backend",
    ]
    return steps
