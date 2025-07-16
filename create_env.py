#!/usr/bin/env python3
"""
Create .env file with Supabase PostgreSQL connection
"""

import os

def create_env_file():
    """Create .env file with the correct database URL"""
    
    env_content = """# Database Configuration
DATABASE_URL=postgresql://postgres.ffykytihaaafystofpli:s%24rsj%24k74Ytz-rA@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

# JWT Configuration
SECRET_KEY=your-secret-key-here-make-it-long-and-secure
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (for future use)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=mahabubn74@gmail.com
SMTP_PASSWORD=qpmiuirtiichvpeq

# App Configuration
APP_NAME=HelpMate API
DEBUG=True
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        print("📝 Database URL: postgresql://postgres.ffykytihaaafystofpli:s%24rsj%24k74Ytz-rA@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

if __name__ == "__main__":
    create_env_file() 