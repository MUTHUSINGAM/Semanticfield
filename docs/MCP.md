# MCP (Model Context Protocol) — SemanticShield AI

## What is MCP?

**MCP (Model Context Protocol)** is an open standard that lets AI applications connect to external data and tools in a uniform way.

Think of it like **USB for AI integrations**:

| Without MCP | With MCP |
|-------------|----------|
| Custom code for each app (Slack, Notion, etc.) | One standard protocol for all apps |
| Different auth/data formats per app | Each app exposes **Resources**, **Tools**, **Prompts** |
| Hard to swap or add sources | Plug in new MCP servers easily |

Official spec: [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## How SemanticShield uses MCP

```
┌─────────────────┐     MCP Resources      ┌──────────────────────┐
│  Slack MCP      │ ── mcp://slack/... ──► │                      │
│  ClickUp MCP    │ ── mcp://clickup/... ► │  SemanticShield AI   │
│  Notion MCP     │ ── mcp://notion/... ─► │  (MCP Client)        │
│  Local Files    │ ── mcp://local/... ──► │                      │
└─────────────────┘                        └──────────┬───────────┘
                                                      │
                                           Chunk → Embed → LanceDB
                                                      │
                                           DLP checks AI responses
```

SemanticShield is the **MCP Client**. Each enterprise app has an **MCP Connector** that exposes data as MCP Resources.

---

## How to tell something IS MCP (in this project)

Look for these identifiers:

| Field | Example | Meaning |
|-------|---------|---------|
| `protocol` | `"mcp"` | Uses Model Context Protocol |
| `mcp_server_id` | `semanticshield-slack-mcp` | Unique MCP server identifier |
| `resource_uri` | `mcp://slack/channels/C123/messages` | MCP Resource URI |
| `connection_type` | `mcp_live` / `mcp_local` / `mock` | How data is fetched |

### In the UI (Data Sources page)
- **MCP Live** badge = real API (Slack, ClickUp, Notion)
- **MCP Local** badge = local files via MCP resource URIs (Excel, PDF)
- **Mock** badge = dummy files only (when `USE_MOCK_ENTERPRISE_DATA=true`)

### In the API
```bash
GET http://localhost:8000/api/sources/mcp-status
```

### In code
```
backend/mcp/
├── base.py              # MCPResource, MCPDocument, MCPConnector interface
├── orchestrator.py      # Fetches from all MCP connectors
├── registry.py          # Lists all connectors
└── connectors/
    ├── slack_connector.py    # server_id: semanticshield-slack-mcp
    ├── clickup_connector.py  # server_id: semanticshield-clickup-mcp
    ├── notion_connector.py   # server_id: semanticshield-notion-mcp
    └── local_files_connector.py
```

---

## Live vs Mock mode

In `.env`:

```env
# false = live MCP connections (Slack, ClickUp, Notion APIs)
USE_MOCK_ENTERPRISE_DATA=false

# Required for live MCP:
SLACK_BOT_TOKEN=xoxb-...
CLICKUP_API_TOKEN=pk_...
CLICKUP_WORKSPACE_ID=...
NOTION_API_KEY=ntn_...
NOTION_DATABASE_ID=...
```

| Source | Live MCP? | How |
|--------|-----------|-----|
| Slack | ✅ Yes | Slack Web API via bot token |
| ClickUp | ✅ Yes | ClickUp REST API |
| Notion | ✅ Yes | Notion API |
| Excel, PDF | 🔵 Local MCP | Files in `data/enterprise/` |
| Gmail, Google Drive | 🔵 Local MCP (for now) | Needs Google OAuth MCP server |

---

## Sync live data

1. Set `USE_MOCK_ENTERPRISE_DATA=false` in `.env`
2. Restart backend
3. Sign in as **Admin** → **Data Sources**
4. Click **Sync Enterprise Data (MCP)**
5. Documents are fetched via MCP connectors → embedded → stored in LanceDB

---

## Fix common MCP connection issues

### Slack — `missing_scope`
In [Slack API Apps](https://api.slack.com/apps) → your app → **OAuth & Permissions**, add:
- `channels:history`
- `channels:read`
- `groups:history`
- `groups:read`

Then **Reinstall to Workspace**. Invite the bot to channels you want to monitor.

### Notion — no pages returned
1. Open your Notion integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Open each page/database → **⋯** → **Connect to** → select your integration
3. Re-run **Sync Enterprise Data (MCP)**

### Gmail / Google Drive — OAuth (future)
Requires Google OAuth MCP server. Currently uses local file exports in `data/enterprise/gmail/` and `google_drive/`.

---

## MCP vs regular API call

| Regular API | MCP |
|-------------|-----|
| `requests.get("slack.com/api/...")` | Connector exposes `list_resources()` + `fetch_documents()` |
| No standard URI | Each document has `mcp://app/resource` URI |
| App-specific only | Any MCP client can connect to same server |
| No discovery | `GET /api/sources/mcp-status` lists all connectors |

Both fetch real data — MCP adds **standard structure** so SemanticShield (and other AI tools) can plug in the same way.
