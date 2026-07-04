from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from models.schemas import TokenResponse, UserLogin, UserResponse, UserRole
from services.auth import create_access_token, get_current_user, serialize_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

DEMO_USERS = {
    "admin@singam.com": {"password": "Admin@123", "full_name": "Admin User", "role": UserRole.ADMIN},
    "security@singam.com": {"password": "Security@123", "full_name": "Security Officer", "role": UserRole.SECURITY_OFFICER},
    "employee@singam.com": {"password": "Employee@123", "full_name": "Employee User", "role": UserRole.EMPLOYEE},
    "auditor@singam.com": {"password": "Auditor@123", "full_name": "Auditor User", "role": UserRole.AUDITOR},
}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": credentials.email.lower()})

    if not user:
        demo = DEMO_USERS.get(credentials.email.lower())
        if demo and credentials.password == demo["password"]:
            raise HTTPException(status_code=401, detail="Demo user not seeded. Run: python seed.py")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return TokenResponse(access_token=token, user=UserResponse(**serialize_user(user)))


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return UserResponse(**serialize_user(user))


@router.get("/demo-credentials")
async def demo_credentials():
    return {
        "demo_mode": True,
        "users": [
            {"email": email, "password": info["password"], "role": info["role"].value, "full_name": info["full_name"]}
            for email, info in DEMO_USERS.items()
        ],
    }
