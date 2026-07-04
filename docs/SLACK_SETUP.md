# Slack MCP Setup — Fix `missing_scope` + Enable Realtime Sync

## Why Slack fails today

Your bot token works (`auth.test` passes) but lacks **Bot Token Scopes** to read channel messages. Slack returns `missing_scope`.

---

## Step-by-step fix (5 minutes)

### 1. Open your Slack app
Go to [https://api.slack.com/apps](https://api.slack.com/apps) → select your app.

### 2. Add Bot Token Scopes
**OAuth & Permissions** → **Scopes** → **Bot Token Scopes** → Add:

| Scope | Purpose |
|-------|---------|
| `channels:read` | List public channels |
| `channels:history` | Read public channel messages |
| `groups:read` | List private channels |
| `groups:history` | Read private channel messages |
| `im:read` | List DMs (optional) |
| `im:history` | Read DMs (optional) |

### 3. Reinstall app
Click **Reinstall to Workspace** at the top of OAuth & Permissions.

### 4. Invite bot to channels
In Slack, run in each channel you want monitored:
```
/invite @YourBotName
```

### 5. Enable Socket Mode (for REALTIME sync)
**Settings** → **Socket Mode** → **Enable**

Create an **App-Level Token** with scope:
- `connections:write`

Copy the `xapp-...` token → put in `.env` as `SLACK_APP_TOKEN`.

### 6. Enable Event Subscriptions
**Event Subscriptions** → **Enable Events**

Subscribe to **Bot Events**:
- `message.channels`
- `message.groups`

### 7. Update `.env` and restart backend
```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
MCP_REALTIME_SYNC_ENABLED=true
MCP_SYNC_INTERVAL_SECONDS=300
```

Restart:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install slack-sdk aiohttp
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Verify in UI
Admin → **Data Sources** — the Slack setup panel shows missing scopes and status.

Or API:
```
GET http://localhost:8000/api/sources/slack/verify
```

---

## Realtime sync — how it works

| Trigger | When |
|---------|------|
| **Slack Socket Mode** | New message in Slack → auto re-sync within 15 seconds |
| **Scheduled** | Every 300 seconds (5 min) — all MCP sources |
| **Manual** | Admin clicks **Sync Now** |
| **Startup** | Backend starts → initial sync |

Check status:
```
GET http://localhost:8000/api/sources/sync-status
```
