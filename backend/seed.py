"""Seed demo users into MongoDB."""
import asyncio

from config import get_settings
from database import get_db
from models.schemas import UserRole
from services.auth import hash_password


async def seed():
    settings = get_settings()
    db = get_db()

    users = [
        {
            "email": settings.admin_email.lower(),
            "password": settings.admin_password,
            "full_name": "Admin User",
            "role": UserRole.ADMIN.value,
        },
        {
            "email": settings.security_officer_email.lower(),
            "password": "Security@123",
            "full_name": "Security Officer",
            "role": UserRole.SECURITY_OFFICER.value,
        },
        {
            "email": settings.employee_email.lower(),
            "password": "Employee@123",
            "full_name": "Employee User",
            "role": UserRole.EMPLOYEE.value,
        },
        {
            "email": settings.auditor_email.lower(),
            "password": "Auditor@123",
            "full_name": "Auditor User",
            "role": UserRole.AUDITOR.value,
        },
    ]

    for user in users:
        existing = await db.users.find_one({"email": user["email"]})
        if existing:
            print(f"  skip  {user['email']} (already exists)")
            continue
        await db.users.insert_one(
            {
                "email": user["email"],
                "password_hash": hash_password(user["password"]),
                "full_name": user["full_name"],
                "role": user["role"],
            }
        )
        print(f"  created {user['email']} / {user['password']} ({user['role']})")

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
