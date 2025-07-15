import sqlite3
import os
from sqlalchemy import create_engine, text
from app.core.database import Base
from app.models import User, Worker, Category, Service, Order, Review, Chat, Message, UserFavorite, WorkerOrder, Notification
from app.models.user import PasswordReset, EmailVerificationToken
from app.core.config import settings

def migrate_database():
    engine = create_engine(settings.database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as connection:
        # Check if password_resets table exists
        result = connection.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='password_resets'
        """))
        if not result.fetchone():
            connection.execute(text("""
                CREATE TABLE password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR NOT NULL,
                    reset_code VARCHAR NOT NULL,
                    user_type VARCHAR NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.execute(text("""
                CREATE INDEX idx_password_resets_email 
                ON password_resets(email)
            """))
            print("Created password_resets table")
        # Check if verification_tokens table exists
        result = connection.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='verification_tokens'
        """))
        if not result.fetchone():
            connection.execute(text("""
                CREATE TABLE verification_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_type VARCHAR NOT NULL,
                    token VARCHAR UNIQUE NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created verification_tokens table")
        connection.commit()
        print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database() 