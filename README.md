# SemanticShield AI

Enterprise AI Data Loss Prevention (AI-DLP) platform — AI Security Gateway between enterprise users and LLMs.

**Live demo reference:** [https://semanticshield-ai-pr-f5q9.bolt.host/](https://semanticshield-ai-pr-f5q9.bolt.host/)

## Quick Start

### 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@singam.com | Admin@123 |
| Security Officer | security@singam.com | Security@123 |
| Employee | employee@singam.com | Employee@123 |
| Auditor | auditor@singam.com | Auditor@123 |

## MCP Live Data

Live MCP mode is enabled (`USE_MOCK_ENTERPRISE_DATA=false` in `.env`).

| Connector | MCP Server ID |
|-----------|---------------|
| Slack | `semanticshield-slack-mcp` |
| ClickUp | `semanticshield-clickup-mcp` |
| Notion | `semanticshield-notion-mcp` |
| Excel, PDF, Gmail, Drive | `semanticshield-localfiles-mcp` |

Admin → **Data Sources** → **Sync Enterprise Data (MCP)** to pull live data.

Full guide: [docs/MCP.md](docs/MCP.md)
