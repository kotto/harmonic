# ──────────────────────────────────────────────
# Bootstrap : créer le premier administrateur
# Usage : python scripts/bootstrap_admin.py --email admin@vital-ka.com --password "motdepasse" --first "Prénom" --last "Nom"
# ──────────────────────────────────────────────
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import async_session_maker, init_db
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus


async def create_admin(email: str, password: str, first_name: str, last_name: str) -> None:
    """Créer le premier compte administrateur."""
    await init_db()

    async with async_session_maker() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"⚠️  Un utilisateur existe déjà avec l'email {email}")
            return

        admin = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        session.add(admin)
        await session.commit()
        print(f"✅ Administrateur créé : {first_name} {last_name} <{email}>")


def main() -> None:
    parser = argparse.ArgumentParser(description="Créer le premier administrateur Vital KA")
    parser.add_argument("--email", required=True, help="Email de l'administrateur")
    parser.add_argument("--password", required=True, help="Mot de passe (min. 8 caractères)")
    parser.add_argument("--first", default="Admin", help="Prénom")
    parser.add_argument("--last", default="Vital KA", help="Nom")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("❌ Le mot de passe doit contenir au moins 8 caractères.")
        sys.exit(1)

    asyncio.run(create_admin(args.email, args.password, args.first, args.last))


if __name__ == "__main__":
    main()