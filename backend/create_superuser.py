#!/usr/bin/env python3
"""
Script to create a superuser account.

Superusers can:
- Approve/reject new user registrations
- Manage all users
- Access admin panel
"""

import sys
import os
import getpass

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.security import get_password_hash
from app.config import get_settings
import uuid

settings = get_settings()


def create_superuser():
    """Create a superuser interactively."""
    print("=" * 60)
    print("Create Superuser Account")
    print("=" * 60)

    # Get email
    while True:
        email = input("\nEmail address: ").strip()
        if not email:
            print("❌ Email cannot be empty")
            continue
        if "@" not in email:
            print("❌ Please enter a valid email address")
            continue
        break

    # Get password
    while True:
        password = getpass.getpass("Password: ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters")
            continue
        password_confirm = getpass.getpass("Password (confirm): ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            continue
        break

    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            print(f"\n⚠️  User with email '{email}' already exists.")

            if existing_user.is_superuser:
                print("   This user is already a superuser.")
                update = input("   Nothing to do. Exit? (y/n): ").lower()
                if update == "y" or update == "":
                    return 0
            else:
                update = input("   Make this user a superuser? (y/n): ").lower()
                if update == "y" or update == "":
                    existing_user.is_superuser = True
                    existing_user.is_approved = True
                    existing_user.is_active = True
                    db.commit()
                    print(f"\n✅ User '{email}' is now a superuser!")
                    return 0
                else:
                    print("   Cancelled.")
                    return 0

        # Create new superuser
        hashed_password = get_password_hash(password)
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_approved=True,  # Superusers are auto-approved
            is_superuser=True,
        )

        db.add(user)
        db.commit()

        print("\n" + "=" * 60)
        print(f"✅ Superuser created successfully!")
        print("=" * 60)
        print(f"\nEmail: {email}")
        print("Permissions: superuser, approved, active")
        print("\nYou can now:")
        print("  1. Login at http://localhost:5173")
        print("  2. Access the admin panel to manage users")
        print("  3. Approve pending user registrations")

        return 0

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating superuser: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(create_superuser())
