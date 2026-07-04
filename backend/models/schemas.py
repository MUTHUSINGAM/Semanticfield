from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    SECURITY_OFFICER = "security_officer"
    EMPLOYEE = "employee"
    AUDITOR = "auditor"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DLPAction(str, Enum):
    ALLOW = "allow"
    MASK = "mask"
    BLOCK = "block"
    HUMAN_REVIEW = "human_review"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.EMPLOYEE


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChatRequest(BaseModel):
    message: str


class MatchedDocument(BaseModel):
    source: str
    title: str
    content: str
    similarity: float
    resource_uri: str | None = None
    connection_type: str | None = None


class ChatResponse(BaseModel):
    prompt: str
    original_response: str
    final_response: str
    risk_level: RiskLevel
    risk_score: float
    action: DLPAction
    matched_documents: list[MatchedDocument] = Field(default_factory=list)
    leak_detected: bool = False
    verification_reason: str = ""


class DashboardStats(BaseModel):
    total_requests: int
    leaks_detected: int
    blocked_responses: int
    masked_responses: int
    human_review_pending: int
    risk_distribution: dict[str, int]
    connected_sources: int


class AuditLogEntry(BaseModel):
    id: str
    user_email: str
    user_role: str
    prompt: str
    ai_response: str
    final_response: str
    matched_source: str
    similarity_score: float
    risk_level: str
    risk_score: float
    action: str
    leak_detected: bool
    timestamp: datetime


class GovernancePolicy(BaseModel):
    risk_low_action: str = "allow"
    risk_medium_action: str = "mask"
    risk_high_action: str = "block"
    risk_critical_action: str = "human_review"
    similarity_threshold: float = 0.75


class EnterpriseSource(BaseModel):
    name: str
    type: str
    status: str
    document_count: int
    last_synced: str | None = None
    connection_type: str = "mock"
    mcp_server_id: str | None = None
    protocol: str = "none"
    resource_uri: str | None = None
    last_error: str | None = None


class ActivityItem(BaseModel):
    id: str
    user_email: str
    action: str
    risk_level: str
    timestamp: datetime
    summary: str
