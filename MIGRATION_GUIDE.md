# HelpMate PostgreSQL Migration Guide

This guide will help you migrate your HelpMate application from SQLite to Supabase PostgreSQL.

## Prerequisites

1. Python 3.8+ installed
2. Access to your Supabase PostgreSQL database
3. Your existing SQLite database (`helpmate.db`)

## Step 1: Install Dependencies

First, install the PostgreSQL driver:

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Create Environment File

Run the script to create your `.env` file:

```bash
python create_env.py
```

This will create a `.env` file with the correct Supabase connection string.

## Step 3: Test Connection

Test the connection to your Supabase database:

```bash
python setup_postgresql.py
```

This script will:
- ✅ Test the connection to Supabase
- ✅ Create all tables in PostgreSQL
- ✅ Migrate data from SQLite to PostgreSQL
- ✅ Verify the migration

## Step 4: Verify Migration

After the migration, you can verify that everything worked:

```bash
# Test the API endpoints
./test_migration.sh
```

## Step 5: Test Your Application

Start your FastAPI application:

```bash
python main.py
```

## Manual Data Addition Commands

If you need to add data manually, here are some curl commands:

### 1. Add a Category
```bash
curl -X POST "http://localhost:8000/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Plumbing",
    "description": "Plumbing services",
    "icon": "plumbing-icon"
  }'
```

### 2. Add a Service
```bash
curl -X POST "http://localhost:8000/services" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pipe Repair",
    "description": "Professional pipe repair service",
    "price": 50.0,
    "category_id": 1,
    "duration": 60
  }'
```

### 3. Add a Worker
```bash
curl -X POST "http://localhost:8000/workers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "address": "123 Main St",
    "skills": ["plumbing", "electrical"],
    "hourly_rate": 25.0,
    "is_available": true
  }'
```

### 4. Add a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+0987654321",
    "password": "password123",
    "address": "456 Oak Ave"
  }'
```

### 5. Add an Order
```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "service_id": 1,
    "worker_id": 1,
    "scheduled_date": "2024-01-15T10:00:00",
    "address": "789 Pine St",
    "description": "Need pipe repair in kitchen",
    "status": "pending"
  }'
```

## Troubleshooting

### Connection Issues
If you get connection errors:

1. **Check your internet connection**
2. **Verify the Supabase credentials** in your `.env` file
3. **Make sure the database is accessible** from your IP

### Migration Issues
If data migration fails:

1. **Check the SQLite database** exists and is readable
2. **Verify table structure** matches between SQLite and PostgreSQL
3. **Check for data type conflicts** (especially dates and booleans)

### Application Issues
If the application doesn't start:

1. **Check the `.env` file** exists and has correct values
2. **Verify all dependencies** are installed
3. **Check the database connection** is working

## Database Schema

The migration will create these tables in PostgreSQL:

- `users` - User accounts and profiles
- `workers` - Service workers
- `categories` - Service categories
- `services` - Available services
- `orders` - Service orders
- `reviews` - User reviews
- `chats` - Chat sessions
- `messages` - Chat messages
- `notifications` - User notifications
- `user_favorites` - User favorite workers
- `worker_orders` - Worker order assignments

## Rollback Plan

If you need to rollback to SQLite:

1. **Update your `.env` file**:
   ```
   DATABASE_URL=sqlite:///./helpmate.db
   ```

2. **Restart your application**:
   ```bash
   python main.py
   ```

## Support

If you encounter any issues during migration:

1. Check the console output for error messages
2. Verify your Supabase connection details
3. Ensure all required dependencies are installed
4. Test the connection manually using the provided scripts

## Next Steps

After successful migration:

1. **Update your frontend** to use the new API endpoints
2. **Test all functionality** thoroughly
3. **Monitor performance** and optimize if needed
4. **Set up backups** for your PostgreSQL database
5. **Consider setting up monitoring** for your Supabase instance 