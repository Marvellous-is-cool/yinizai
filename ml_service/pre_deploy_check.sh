#!/bin/bash

# 🚀 Pre-deployment Checklist Script
# Run this before deploying to production

echo "🔍 Pre-deployment Checklist for Yinizai ML Service"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for checks
passed=0
failed=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "✅ ${GREEN}$1 exists${NC}"
        ((passed++))
    else
        echo -e "❌ ${RED}$1 is missing${NC}"
        ((failed++))
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        echo -e "✅ ${GREEN}$1 is executable${NC}"
        ((passed++))
    else
        echo -e "❌ ${RED}$1 is not executable${NC}"
        echo -e "   ${YELLOW}Fix with: chmod +x $1${NC}"
        ((failed++))
    fi
}

check_env_var() {
    if grep -q "$1" .env.production 2>/dev/null; then
        echo -e "✅ ${GREEN}Environment variable $1 configured${NC}"
        ((passed++))
    else
        echo -e "⚠️  ${YELLOW}Environment variable $1 not found in .env.production${NC}"
    fi
}

echo ""
echo "📁 Checking Required Files..."
echo "----------------------------"

# Core application files
check_file "main.py"
check_file "requirements.txt"
check_file "DATABASE_SCHEMA.sql"
check_file "API_DOCUMENTATION.md"

# Deployment files
check_file "build.sh"
check_file "start_production.sh"
check_file "render.yaml"
check_file ".env.production"
check_file "setup_production_db.py"

echo ""
echo "🔧 Checking Script Permissions..."
echo "--------------------------------"

check_executable "build.sh"
check_executable "start_production.sh"
check_executable "setup_production_db.py"

echo ""
echo "⚙️  Checking Environment Configuration..."
echo "----------------------------------------"

check_env_var "DB_HOST"
check_env_var "DB_USER"
check_env_var "DB_PASSWORD"
check_env_var "SECRET_KEY"
check_env_var "ENVIRONMENT"

echo ""
echo "📦 Checking Python Dependencies..."
echo "---------------------------------"

if [ -f "requirements.txt" ]; then
    echo "Checking for production-critical packages:"
    
    if grep -q "fastapi" requirements.txt; then
        echo -e "✅ ${GREEN}FastAPI found${NC}"
        ((passed++))
    else
        echo -e "❌ ${RED}FastAPI not in requirements.txt${NC}"
        ((failed++))
    fi
    
    if grep -q "gunicorn" requirements.txt; then
        echo -e "✅ ${GREEN}Gunicorn found${NC}"
        ((passed++))
    else
        echo -e "❌ ${RED}Gunicorn not in requirements.txt${NC}"
        ((failed++))
    fi
    
    if grep -q "cryptography" requirements.txt; then
        echo -e "✅ ${GREEN}Cryptography found${NC}"
        ((passed++))
    else
        echo -e "❌ ${RED}Cryptography not in requirements.txt${NC}"
        ((failed++))
    fi
    
    if grep -q "mysql-connector-python" requirements.txt; then
        echo -e "✅ ${GREEN}MySQL connector found${NC}"
        ((passed++))
    else
        echo -e "❌ ${RED}MySQL connector not in requirements.txt${NC}"
        ((failed++))
    fi
fi

echo ""
echo "🗃️  Checking Database Schema..."
echo "------------------------------"

if [ -f "DATABASE_SCHEMA.sql" ]; then
    if grep -q "CREATE TABLE" DATABASE_SCHEMA.sql; then
        echo -e "✅ ${GREEN}Database schema contains table definitions${NC}"
        ((passed++))
    else
        echo -e "❌ ${RED}Database schema appears incomplete${NC}"
        ((failed++))
    fi
    
    # Check for required tables
    required_tables=("questions" "student_answers" "question_analytics")
    for table in "${required_tables[@]}"; do
        if grep -q "$table" DATABASE_SCHEMA.sql; then
            echo -e "✅ ${GREEN}Table '$table' found in schema${NC}"
            ((passed++))
        else
            echo -e "❌ ${RED}Table '$table' missing from schema${NC}"
            ((failed++))
        fi
    done
fi

echo ""
echo "🌐 Checking CORS Configuration..."
echo "--------------------------------"

if grep -q "CORSMiddleware" main.py 2>/dev/null; then
    echo -e "✅ ${GREEN}CORS middleware configured${NC}"
    ((passed++))
else
    echo -e "⚠️  ${YELLOW}CORS middleware not found - may cause frontend issues${NC}"
fi

echo ""
echo "🔐 Security Checks..."
echo "--------------------"

# Check for hardcoded secrets
if grep -r "password.*=" . --exclude-dir=.git --exclude="*.md" --exclude="pre_deploy_check.sh" 2>/dev/null | grep -v "DB_PASSWORD" | grep -v "your_password"; then
    echo -e "⚠️  ${YELLOW}Potential hardcoded passwords found. Please review.${NC}"
else
    echo -e "✅ ${GREEN}No obvious hardcoded passwords found${NC}"
    ((passed++))
fi

# Check for debug mode
if grep -q "debug.*=.*True" main.py 2>/dev/null; then
    echo -e "⚠️  ${YELLOW}Debug mode may be enabled. Should be False for production.${NC}"
else
    echo -e "✅ ${GREEN}No debug mode found in main.py${NC}"
    ((passed++))
fi

echo ""
echo "📊 Summary"
echo "=========="
echo -e "✅ Passed: ${GREEN}$passed${NC}"
echo -e "❌ Failed: ${RED}$failed${NC}"

echo ""
if [ $failed -eq 0 ]; then
    echo -e "🎉 ${GREEN}All checks passed! Ready for deployment.${NC}"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Push your code to GitHub"
    echo "2. Create Aiven MySQL service"
    echo "3. Deploy to Render"
    echo "4. Set environment variables in Render"
    echo "5. Run database initialization"
    echo ""
    echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions."
    exit 0
else
    echo -e "⚠️  ${YELLOW}$failed issues found. Please fix them before deploying.${NC}"
    echo ""
    echo "🔧 Common Fixes:"
    echo "- chmod +x *.sh  (make scripts executable)"
    echo "- Review requirements.txt for missing packages"
    echo "- Check .env.production for all required variables"
    echo "- Ensure DATABASE_SCHEMA.sql is complete"
    exit 1
fi
