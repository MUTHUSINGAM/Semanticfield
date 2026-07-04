from datetime import datetime, timezone
from typing import Any

from config import get_settings
from database import get_db
from models.schemas import (
    ChatResponse,
    DLPAction,
    DashboardStats,
    GovernancePolicy,
    MatchedDocument,
    RiskLevel,
)
from services.dlp import (
    apply_action_to_response,
    apply_governance,
    calculate_risk_score,
    score_to_risk_level,
    verify_leak_with_llm,
)
from services.llm import generate_llm_response
from services.vector_store import vector_store


async def get_policies() -> dict[str, Any]:
    db = get_db()
    doc = await db.policies.find_one({"_id": "governance"})
    if doc:
        return doc
    settings = get_settings()
    default = {
        "_id": "governance",
        "risk_low_action": settings.risk_low_action,
        "risk_medium_action": settings.risk_medium_action,
        "risk_high_action": settings.risk_high_action,
        "risk_critical_action": settings.risk_critical_action,
        "similarity_threshold": settings.similarity_threshold,
    }
    await db.policies.insert_one(default)
    return default


async def process_chat(user: dict[str, Any], message: str) -> ChatResponse:
    settings = get_settings()
    policies = await get_policies()

    original_response = await generate_llm_response(message)
    prompt_matches = await vector_store.search(message, settings.top_k_matches)
    response_matches = await vector_store.search(original_response, settings.top_k_matches)

    seen = set()
    matches: list[dict] = []
    for m in sorted(prompt_matches + response_matches, key=lambda x: x["similarity"], reverse=True):
        key = f"{m['source']}:{m['title']}"
        if key not in seen:
            seen.add(key)
            matches.append(m)

    threshold = float(policies.get("similarity_threshold", settings.similarity_threshold))
    relevant_matches = [m for m in matches if m["similarity"] >= threshold - 0.25]

    leak_detected, verification_reason = await verify_leak_with_llm(original_response, relevant_matches, message)

    top_classification = relevant_matches[0]["classification"] if relevant_matches else "public"
    top_similarity = relevant_matches[0]["similarity"] if relevant_matches else 0.0

    risk_score = calculate_risk_score(top_similarity, leak_detected, top_classification)
    if leak_detected:
        risk_score = max(risk_score, 72.0 if top_classification == "highly_confidential" else 58.0)
    elif top_similarity < threshold:
        risk_score = min(risk_score, 35.0)

    risk_level = score_to_risk_level(risk_score)
    policy_map = {
        "LOW": policies.get("risk_low_action", settings.risk_low_action),
        "MEDIUM": policies.get("risk_medium_action", settings.risk_medium_action),
        "HIGH": policies.get("risk_high_action", settings.risk_high_action),
        "CRITICAL": policies.get("risk_critical_action", settings.risk_critical_action),
    }
    action = apply_governance(risk_level, policy_map)
    final_response = apply_action_to_response(original_response, action)

    matched_docs = [
        MatchedDocument(
            source=m["source"],
            title=m["title"],
            content=m["content"][:300],
            similarity=m["similarity"],
            resource_uri=m.get("resource_uri") or None,
            connection_type=m.get("connection_type") or None,
        )
        for m in relevant_matches[:3]
    ]

    await _log_event(user, message, original_response, final_response, relevant_matches, risk_level, risk_score, action, leak_detected)

    return ChatResponse(
        prompt=message,
        original_response=original_response,
        final_response=final_response,
        risk_level=risk_level,
        risk_score=risk_score,
        action=action,
        matched_documents=matched_docs,
        leak_detected=leak_detected,
        verification_reason=verification_reason,
    )


async def _log_event(
    user: dict,
    prompt: str,
    ai_response: str,
    final_response: str,
    matches: list[dict],
    risk_level: RiskLevel,
    risk_score: float,
    action: DLPAction,
    leak_detected: bool,
) -> None:
    db = get_db()
    top = matches[0] if matches else {}
    await db.audit_logs.insert_one(
        {
            "user_id": str(user["_id"]),
            "user_email": user["email"],
            "user_role": user["role"],
            "prompt": prompt,
            "ai_response": ai_response,
            "final_response": final_response,
            "matched_source": top.get("source", "none"),
            "matched_title": top.get("title", ""),
            "matched_resource_uri": top.get("resource_uri", ""),
            "matched_connection_type": top.get("connection_type", ""),
            "similarity_score": top.get("similarity", 0.0),
            "risk_level": risk_level.value,
            "risk_score": risk_score,
            "action": action.value,
            "leak_detected": leak_detected,
            "timestamp": datetime.now(timezone.utc),
        }
    )


async def get_dashboard_stats() -> DashboardStats:
    db = get_db()
    total = await db.audit_logs.count_documents({})
    leaks = await db.audit_logs.count_documents({"leak_detected": True})
    blocked = await db.audit_logs.count_documents({"action": "block"})
    masked = await db.audit_logs.count_documents({"action": "mask"})
    review = await db.audit_logs.count_documents({"action": "human_review"})

    pipeline = [{"$group": {"_id": "$risk_level", "count": {"$sum": 1}}}]
    risk_dist: dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    async for row in db.audit_logs.aggregate(pipeline):
        if row["_id"] in risk_dist:
            risk_dist[row["_id"]] = row["count"]

    sources = await db.enterprise_sources.count_documents({"status": "connected"})

    return DashboardStats(
        total_requests=total,
        leaks_detected=leaks,
        blocked_responses=blocked,
        masked_responses=masked,
        human_review_pending=review,
        risk_distribution=risk_dist,
        connected_sources=sources or 7,
    )
