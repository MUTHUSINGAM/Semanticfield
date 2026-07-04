import re
from typing import Any

from config import get_settings
from models.schemas import DLPAction, RiskLevel
from services.embeddings import keyword_overlap_score

SENSITIVE_PATTERNS = [
    r"\b(salary|compensation|payroll|bonus)\b",
    r"\b(api[_\s]?key|secret|password|token)\b",
    r"\b(revenue|profit|forecast|budget)\b",
    r"\b(contract|nda|confidential)\b",
    r"\b(roadmap|release plan|sprint)\b",
    r"\b(hr policy|termination|performance review)\b",
]


def calculate_risk_score(similarity: float, leak_confirmed: bool, classification: str) -> float:
    base = similarity * 100
    if leak_confirmed:
        base += 15
    if classification == "highly_confidential":
        base += 10
    return min(100.0, round(base, 2))


def score_to_risk_level(score: float) -> RiskLevel:
    if score >= 85:
        return RiskLevel.CRITICAL
    if score >= 70:
        return RiskLevel.HIGH
    if score >= 50:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def apply_governance(risk_level: RiskLevel, policies: dict[str, str] | None = None) -> DLPAction:
    settings = get_settings()
    policy_map = policies or {
        "LOW": settings.risk_low_action,
        "MEDIUM": settings.risk_medium_action,
        "HIGH": settings.risk_high_action,
        "CRITICAL": settings.risk_critical_action,
    }
    action_str = policy_map.get(risk_level.value, "allow")
    return DLPAction(action_str)


def mask_sensitive_text(text: str) -> str:
    masked = text
    masked = re.sub(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:USD|INR|₹|\$)?\b", "[REDACTED_AMOUNT]", masked)
    masked = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]", masked)
    masked = re.sub(r"\bsk-[A-Za-z0-9]{10,}\b", "[REDACTED_API_KEY]", masked)
    masked = re.sub(r"\b(Ravi|Priya|Ananya|Karthik|Meera)\b['']?s?\s+(salary|compensation)", r"\1's [REDACTED]", masked, flags=re.IGNORECASE)
    return masked


def rule_based_leak_check(ai_response: str, matched_docs: list[dict[str, Any]], prompt: str = "") -> tuple[bool, str]:
    if not matched_docs:
        if re.search(r"\b(salary|compensation|payroll)\b", prompt, re.IGNORECASE) and re.search(
            r"[\d,]+(?:\.\d+)?\s*(?:₹|INR|\$)?|\b\d{6,}\b", ai_response
        ):
            return True, "Response discloses numeric compensation data matching a confidential query."
        return False, "No confidential document matches found."

    top = max(matched_docs, key=lambda d: keyword_overlap_score(ai_response, d["content"]))
    overlap = keyword_overlap_score(ai_response, top["content"])
    prompt_overlap = keyword_overlap_score(prompt, top["content"]) if prompt else 0
    sensitive_hits = sum(1 for p in SENSITIVE_PATTERNS if re.search(p, ai_response, re.IGNORECASE))

    if top["similarity"] >= 0.55 and overlap >= 0.08:
        return True, f"Semantic overlap ({top['similarity']:.0%}) with {top['source']} document '{top['title']}'."

    if prompt_overlap >= 0.08 and overlap >= 0.08:
        return True, f"Confidential {top['source']} data referenced in response to sensitive query."

    if sensitive_hits >= 1 and top["similarity"] >= 0.35:
        return True, f"Response contains sensitive terms matching {top['source']} content."

    if overlap >= 0.12:
        return True, f"Paraphrased leak detected via keyword overlap with '{top['title']}'."

    return False, "No leak confirmed after verification."


async def verify_leak_with_llm(ai_response: str, matched_docs: list[dict[str, Any]], user_prompt: str = "") -> tuple[bool, str]:
    settings = get_settings()
    if not settings.has_openai_key or not matched_docs:
        return rule_based_leak_check(ai_response, matched_docs, user_prompt)

    context = "\n\n".join(
        f"Source: {d['source']}\nTitle: {d['title']}\nContent: {d['content'][:500]}"
        for d in matched_docs[:3]
    )
    verification_prompt = (
        "You are an enterprise AI-DLP verifier. Determine if the AI response leaks confidential "
        "information from the enterprise documents (including paraphrased leaks).\n\n"
        f"AI Response:\n{ai_response}\n\nConfidential Documents:\n{context}\n\n"
        'Reply with JSON only: {"leak_detected": true/false, "reason": "..."}'
    )
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_verification_model,
            messages=[{"role": "user", "content": verification_prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        import json

        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            return bool(parsed.get("leak_detected")), str(parsed.get("reason", ""))
    except Exception:
        pass

    return rule_based_leak_check(ai_response, matched_docs, user_prompt)


def apply_action_to_response(original: str, action: DLPAction) -> str:
    if action == DLPAction.ALLOW:
        return original
    if action == DLPAction.MASK:
        return mask_sensitive_text(original)
    if action == DLPAction.BLOCK:
        return (
            "⛔ This response was blocked by SemanticShield AI because it may contain "
            "confidential enterprise information. Please rephrase your question or contact IT Security."
        )
    if action == DLPAction.HUMAN_REVIEW:
        return (
            "🔒 This response requires human review by the Security team before it can be delivered. "
            "Your request has been logged for audit."
        )
    return original
