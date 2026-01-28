#!/usr/bin/env python3
"""
Migration script to add password_reset_tokens table to the database.

This script creates the password_reset_tokens table for storing password reset tokens.
Run this script after updating the models to add password reset functionality.

Usage:
    python3 migrate_add_password_reset.py
"""

import sqlite3
import os
import sys


def run_migration():
    """Run the migration to add password reset tokens table."""

    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), "storage", "scorescan.db")

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Please ensure the database exists before running migrations.")
        sys.exit(1)

    print(f"🔍 Found database at: {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_tokens'"
        )
        if cursor.fetchone():
            print(
                "✅ Table 'password_reset_tokens' already exists. No migration needed."
            )
            return

        print("📝 Creating 'password_reset_tokens' table...")

        # Create password_reset_tokens table
        cursor.execute("""
            CREATE TABLE password_reset_tokens (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                token VARCHAR(64) UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL,
                used VARCHAR(1) DEFAULT '0',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Create indexes for faster lookups
        print("📝 Creating indexes...")
        cursor.execute(
            "CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token)"
        )
        cursor.execute(
            "CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id)"
        )

        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - Created 'password_reset_tokens' table")
        print("   - Created indexes for token and user_id")

    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Password Reset Tokens Table Migration")
    print("=" * 70)
    print()

    run_migration()

    print()
    print("=" * 70)
    print("Migration Complete")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Configure SMTP settings in .env file:")
    print("   - SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD")
    print("   - SMTP_FROM_EMAIL, FRONTEND_URL")
    print("2. Restart the backend server")
    print("3. Test password reset functionality")
