#!/bin/bash

# HelpMate PostgreSQL Migration Test Script
# This script tests the migration and provides curl commands to add data

echo "🧪 Testing HelpMate PostgreSQL Migration"
echo "========================================"

# Base URL
BASE_URL="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-""}
    
    echo -e "\n${YELLOW}Testing $method $endpoint${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✅ Success ($http_code)${NC}"
        cat /tmp/response.json | python3 -m json.tool 2>/dev/null || cat /tmp/response.json
    else
        echo -e "${RED}❌ Failed ($http_code)${NC}"
        cat /tmp/response.json
    fi
}

# Test basic endpoints
echo -e "\n${YELLOW}1. Testing basic endpoints...${NC}"
test_endpoint "/"
test_endpoint "/docs"

# Test categories endpoint
echo -e "\n${YELLOW}2. Testing categories...${NC}"
test_endpoint "/categories"

# Test services endpoint
echo -e "\n${YELLOW}3. Testing services...${NC}"
test_endpoint "/services"

# Test workers endpoint
echo -e "\n${YELLOW}4. Testing workers...${NC}"
test_endpoint "/workers"

# Test users endpoint
echo -e "\n${YELLOW}5. Testing users...${NC}"
test_endpoint "/users"

echo -e "\n${GREEN}🎉 Basic migration test completed!${NC}"

echo -e "\n${YELLOW}📋 Manual Test Commands:${NC}"
echo "=================================="

echo -e "\n${GREEN}1. Test Categories:${NC}"
echo "curl -X GET \"$BASE_URL/categories\""

echo -e "\n${GREEN}2. Test Services:${NC}"
echo "curl -X GET \"$BASE_URL/services\""

echo -e "\n${GREEN}3. Test Workers:${NC}"
echo "curl -X GET \"$BASE_URL/workers\""

echo -e "\n${GREEN}4. Test Users:${NC}"
echo "curl -X GET \"$BASE_URL/users\""

echo -e "\n${GREEN}5. Test Orders:${NC}"
echo "curl -X GET \"$BASE_URL/orders\""

echo -e "\n${GREEN}6. Test Admin Panel:${NC}"
echo "curl -X GET \"$BASE_URL/admin/orders\""

echo -e "\n${YELLOW}📝 Add Data Commands:${NC}"
echo "=============================="

echo -e "\n${GREEN}1. Add a Category:${NC}"
echo 'curl -X POST "'$BASE_URL'/categories" \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "name": "Plumbing",
    "description": "Plumbing services",
    "icon": "plumbing-icon"
  }'"'"''

echo -e "\n${GREEN}2. Add a Service:${NC}"
echo 'curl -X POST "'$BASE_URL'/services" \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "name": "Pipe Repair",
    "description": "Professional pipe repair service",
    "price": 50.0,
    "category_id": 1,
    "duration": 60
  }'"'"''

echo -e "\n${GREEN}3. Add a Worker:${NC}"
echo 'curl -X POST "'$BASE_URL'/workers" \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "address": "123 Main St",
    "skills": ["plumbing", "electrical"],
    "hourly_rate": 25.0,
    "is_available": true
  }'"'"''

echo -e "\n${GREEN}4. Add a User:${NC}"
echo 'curl -X POST "'$BASE_URL'/auth/register" \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+0987654321",
    "password": "password123",
    "address": "456 Oak Ave"
  }'"'"''

echo -e "\n${GREEN}5. Add an Order:${NC}"
echo 'curl -X POST "'$BASE_URL'/orders" \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "user_id": 1,
    "service_id": 1,
    "worker_id": 1,
    "scheduled_date": "2024-01-15T10:00:00",
    "address": "789 Pine St",
    "description": "Need pipe repair in kitchen",
    "status": "pending"
  }'"'"''

echo -e "\n${YELLOW}🔧 Troubleshooting:${NC}"
echo "======================"
echo "1. If connection fails, check if PostgreSQL is running:"
echo "   brew services list | grep postgresql"
echo ""
echo "2. If database connection fails, check your .env file:"
echo "   DATABASE_URL=postgresql://postgres:password@localhost:5432/helpmate_db"
echo ""
echo "3. To restart PostgreSQL:"
echo "   brew services restart postgresql@14"
echo ""
echo "4. To check database tables:"
echo "   psql -U postgres -d helpmate_db -c \"\\dt\"" 