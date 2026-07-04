import re
from typing import Any

from config import get_settings


KNOWLEDGE_BASE: list[dict[str, str]] = [
    {
        "keywords": ["ravi", "salary"],
        "response": "Ravi Kumar's annual salary is ₹18,50,000 with a Q4 performance bonus of ₹2,00,000. This information is from the confidential payroll sheet.",
    },
    {
        "keywords": ["priya", "salary"],
        "response": "Priya Sharma earns ₹22,00,000 per year as Senior Product Manager, plus ESOP grants worth approximately ₹8,00,000.",
    },
    {
        "keywords": ["ananya", "salary"],
        "response": "Ananya Reddy's compensation package is ₹16,75,000 annually as a Data Engineer in the Bangalore office.",
    },
    {
        "keywords": ["api key", "production", "stripe"],
        "response": "The production Stripe API key is sk-live-51SingamTech2026ProdKey9Xk2mN8pQ and must not be shared externally.",
    },
    {
        "keywords": ["q3", "revenue", "forecast"],
        "response": "Q3 revenue forecast projects ₹42.5 Cr with 18% YoY growth. EBITDA margin target is 24%. This is from the confidential finance report.",
    },
    {
        "keywords": ["roadmap", "2026", "product"],
        "response": "The 2026 product roadmap includes AI Security Gateway v2.0 in Q2, MCP connector expansion in Q3, and enterprise SSO in Q4. Launch is currently marked confidential.",
    },
    {
        "keywords": ["acme", "contract"],
        "response": "The Acme Corp enterprise contract value is ₹3.2 Cr over 3 years with a 15% annual uplift clause, signed under NDA.",
    },
    {
        "keywords": ["layoff", "hr", "policy"],
        "response": "The internal HR policy document outlines a planned 8% workforce optimization in Engineering by Q1 2027. This has not been announced publicly.",
    },
    {
        "keywords": ["slack", "finance"],
        "response": "In the #finance-leadership Slack channel, the CFO mentioned that Singam's runway extends to 2028 with current burn rate of ₹1.2 Cr/month.",
    },
]


async def generate_llm_response(user_message: str) -> str:
    settings = get_settings()

    if settings.has_openai_key:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            system_prompt = (
                "You are an AI assistant for Singam Technologies employees. "
                "Answer helpfully using general knowledge. If you don't know, say so."
            )
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content or "I couldn't generate a response."
        except Exception:
            pass

    return _demo_response(user_message)


def _demo_response(user_message: str) -> str:
    message_lower = user_message.lower()

    best_match: dict[str, str] | None = None
    best_score = 0
    for entry in KNOWLEDGE_BASE:
        score = sum(1 for kw in entry["keywords"] if kw in message_lower)
        if score > best_score:
            best_score = score
            best_match = entry

    if best_match and best_score >= 1:
        return best_match["response"]

    if re.search(r"\b(salary|compensation|payroll)\b", message_lower):
        return (
            "Based on internal records, employee compensation varies by role and level. "
            "For specific salary details, please contact HR directly through the internal portal."
        )

    if re.search(r"\b(hello|hi|hey|help)\b", message_lower):
        return (
            "Hello! I'm the Singam Technologies AI Assistant. I can help with product questions, "
            "engineering docs, and general company information. How can I help you today?"
        )

    return (
        "I can help with Singam Technologies internal topics including engineering, product, "
        "and general company policies. Could you provide more details about what you need?"
    )
