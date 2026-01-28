#!/usr/bin/env python3
"""
Database migration script to add is_approved and is_superuser fields to users table.

This migration:
1. Adds is_approved column (defaults to False for new users)
2. Adds is_superuser column (defaults to False)
3. Sets existing users to approved=True (grandfather existing users)
4. Does NOT create a superuser (use create_superuser.py for that)
"""

import sqlite3
import sys
import os

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), "storage", "scorescan.db")


def migrate():
    """Run the migration."""
    print("=" * 60)
    print("User Approval Migration")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        print("   The database will be created when you start the application.")
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        needs_is_approved = "is_approved" not in columns
        needs_is_superuser = "is_superuser" not in columns

        if not needs_is_approved and not needs_is_superuser:
            print("✓ Migration already applied - nothing to do")
            return 0

        # Add is_approved column
        if needs_is_approved:
            print("\n1. Adding 'is_approved' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0")

            # Set existing users to approved (grandfather clause)
            cursor.execute("UPDATE users SET is_approved = 1")
            count = cursor.rowcount
            print(f"   ✓ Added is_approved column")
            print(f"   ✓ Approved {count} existing user(s)")

        # Add is_superuser column
        if needs_is_superuser:
            print("\n2. Adding 'is_superuser' column...")
            cursor.execute(
                "ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT 0"
            )
            print("   ✓ Added is_superuser column")

        conn.commit()

        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)

        # Show current users
        cursor.execute("SELECT email, is_approved, is_superuser FROM users")
        users = cursor.fetchall()

        if users:
            print(f"\nCurrent users ({len(users)}):")
            for email, approved, superuser in users:
                status = []
                if approved:
                    status.append("approved")
                if superuser:
                    status.append("superuser")
                status_str = ", ".join(status) if status else "pending approval"
                print(f"  - {email} ({status_str})")
        else:
            print("\nNo users in database yet.")

        print("\nNext steps:")
        print("  1. Create a superuser: python3 create_superuser.py")
        print("  2. Restart the application: docker-compose restart")

        return 0

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(migrate())
