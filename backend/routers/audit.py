from fastapi import APIRouter, Depends

from database import get_db
from models.schemas import AuditLogEntry, GovernancePolicy, UserRole
from services.auth import require_roles
from services.chat import get_policies

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/audit-logs", response_model=list[AuditLogEntry])
async def audit_logs(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER, UserRole.AUDITOR))):
    db = get_db()
    cursor = db.audit_logs.find().sort("timestamp", -1).limit(100)
    logs: list[AuditLogEntry] = []
    async for doc in cursor:
        logs.append(
            AuditLogEntry(
                id=str(doc["_id"]),
                user_email=doc["user_email"],
                user_role=doc["user_role"],
                prompt=doc["prompt"],
                ai_response=doc["ai_response"],
                final_response=doc["final_response"],
                matched_source=doc.get("matched_source", "none"),
                similarity_score=doc.get("similarity_score", 0.0),
                risk_level=doc["risk_level"],
                risk_score=doc.get("risk_score", 0.0),
                action=doc["action"],
                leak_detected=doc.get("leak_detected", False),
                timestamp=doc["timestamp"],
            )
        )
    return logs


@router.get("/policies", response_model=GovernancePolicy)
async def get_governance_policies(_user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER))):
    doc = await get_policies()
    return GovernancePolicy(
        risk_low_action=doc.get("risk_low_action", "allow"),
        risk_medium_action=doc.get("risk_medium_action", "mask"),
        risk_high_action=doc.get("risk_high_action", "block"),
        risk_critical_action=doc.get("risk_critical_action", "human_review"),
        similarity_threshold=doc.get("similarity_threshold", 0.75),
    )


@router.put("/policies", response_model=GovernancePolicy)
async def update_policies(
    policy: GovernancePolicy,
    _user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER)),
):
    db = get_db()
    update = policy.model_dump()
    await db.policies.update_one({"_id": "governance"}, {"$set": update}, upsert=True)
    return policy
