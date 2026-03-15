"""Create a test account for testing the application"""
import asyncio
from app.database import async_engine, Base
from app.models import User
from app.auth import hash_password
from sqlalchemy import select

async def create_test_account():
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test user
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == "test@legallens.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ Test account already exists!")
            print(f"   Email: test@legallens.com")
            print(f"   Password: Test123!")
            print(f"   Tier: {existing_user.subscription_tier}")
            return
        
        # Create new user
        test_user = User(
            email="test@legallens.com",
            full_name="Test User",
            hashed_password=hash_password("Test123!"),
            subscription_tier="pro",  # Give pro tier for testing
            is_active=True
        )
        session.add(test_user)
        await session.commit()
        
        print("🎉 Test account created successfully!")
        print(f"   Email: test@legallens.com")
        print(f"   Password: Test123!")
        print(f"   Tier: Pro (unlimited documents)")

if __name__ == "__main__":
    asyncio.run(create_test_account())
