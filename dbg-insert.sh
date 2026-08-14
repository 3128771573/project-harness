#!/bin/bash
sudo docker exec harness-backend python - <<'PY' 2>&1
import asyncio, sys
sys.path.insert(0, "/app/backend")
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

async def main():
    async with SessionLocal() as db:
        for uname in ("g1user", "g2user", "g3user"):
            exists = (await db.execute(select(User).where(User.email == f"{uname}@example.com"))).scalar_one_or_none()
            if exists is None:
                db.add(User(username=uname, email=f"{uname}@example.com", password_hash=hash_password("TestPass123")))
        await db.commit()
        print("users ready")

asyncio.run(main())
PY
echo "exit=$?"
