from datetime import datetime

from fastapi import APIRouter, Depends

from database import get_db
from models.schemas import ActivityItem, DashboardStats, UserRole
from services.auth import require_roles
from services.chat import get_dashboard_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def stats(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER, UserRole.AUDITOR))):
    return await get_dashboard_stats()


@router.get("/recent-activities", response_model=list[ActivityItem])
async def recent_activities(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER, UserRole.AUDITOR))):
    db = get_db()
    cursor = db.audit_logs.find().sort("timestamp", -1).limit(10)
    items: list[ActivityItem] = []
    async for doc in cursor:
        items.append(
            ActivityItem(
                id=str(doc["_id"]),
                user_email=doc["user_email"],
                action=doc["action"],
                risk_level=doc["risk_level"],
                timestamp=doc["timestamp"],
                summary=f"{doc['action'].upper()} — {doc.get('matched_source', 'none')} (score: {doc.get('risk_score', 0)})",
            )
        )
    return items


@router.get("/top-sources")
async def top_sources(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER))):
    db = get_db()
    pipeline = [
        {"$match": {"matched_source": {"$ne": "none"}}},
        {"$group": {"_id": "$matched_source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 7},
    ]
    results = []
    async for row in db.audit_logs.aggregate(pipeline):
        results.append({"source": row["_id"], "alerts": row["count"]})
    if not results:
        return [
            {"source": "Excel", "alerts": 0},
            {"source": "Slack", "alerts": 0},
            {"source": "Google Drive", "alerts": 0},
            {"source": "Notion", "alerts": 0},
            {"source": "ClickUp", "alerts": 0},
            {"source": "Gmail", "alerts": 0},
            {"source": "PDF", "alerts": 0},
        ]
    return results
