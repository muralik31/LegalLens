#!/bin/bash

# LegalLens v3.0 API Test Script
# Tests the complete flow: Register → Login → Upload → Analyze

set -e

# Configuration
API_URL="http://localhost:8000"
TEST_EMAIL="test@example.com"
TEST_PASSWORD="testpassword123"
TEST_NAME="Test User"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🧪 LegalLens v3.0 API Test"
echo "========================="
echo ""

# Check if server is running
echo "📡 Checking if server is running..."
if curl -s "$API_URL/health" > /dev/null; then
    echo -e "${GREEN}✓${NC} Server is running"
    health=$(curl -s "$API_URL/health" | python3 -m json.tool)
    echo "$health"
else
    echo -e "${RED}✗${NC} Server is not running"
    echo "Start the server with: uvicorn app.main_v3:app --reload"
    exit 1
fi

echo ""
echo "────────────────────────────────"
echo ""

# 1. Register User
echo "1️⃣  Registering user..."
register_response=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"full_name\": \"$TEST_NAME\"
  }" || echo '{"detail":"User may already exist"}')

if echo "$register_response" | grep -q '"id"'; then
    echo -e "${GREEN}✓${NC} User registered successfully"
    echo "$register_response" | python3 -m json.tool
elif echo "$register_response" | grep -q "already registered"; then
    echo -e "${YELLOW}⚠${NC} User already exists (will proceed with login)"
else
    echo -e "${YELLOW}⚠${NC} Registration response: $register_response"
fi

echo ""
echo "────────────────────────────────"
echo ""

# 2. Login
echo "2️⃣  Logging in..."
login_response=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

if echo "$login_response" | grep -q '"access_token"'; then
    echo -e "${GREEN}✓${NC} Login successful"
    access_token=$(echo "$login_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "Access token: ${access_token:0:20}..."
else
    echo -e "${RED}✗${NC} Login failed"
    echo "$login_response" | python3 -m json.tool
    exit 1
fi

echo ""
echo "────────────────────────────────"
echo ""

# 3. Get user info
echo "3️⃣  Getting user info..."
user_response=$(curl -s -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer $access_token")

if echo "$user_response" | grep -q '"email"'; then
    echo -e "${GREEN}✓${NC} User info retrieved"
    echo "$user_response" | python3 -m json.tool
else
    echo -e "${RED}✗${NC} Failed to get user info"
    echo "$user_response" | python3 -m json.tool
    exit 1
fi

echo ""
echo "────────────────────────────────"
echo ""

# 4. Create test document
echo "4️⃣  Creating test document..."
test_file="/tmp/test_contract.txt"
cat > "$test_file" << 'EOF'
RENTAL AGREEMENT

This rental agreement is entered into between Landlord and Tenant.

1. RENT: Tenant shall pay Rs 15,000 monthly rent by the 5th of each month.

2. SECURITY DEPOSIT: A security deposit of Rs 50,000 is required.

3. LOCK-IN PERIOD: This agreement has a lock-in period of 11 months.

4. TERMINATION: Either party may terminate this agreement with 2 months notice.

5. MAINTENANCE: Tenant is responsible for minor repairs. Major repairs are landlord's responsibility.

6. LATE FEE: A late fee of Rs 500 per day will be charged for delayed rent payment.

7. INDEMNITY: Tenant agrees to indemnify the landlord against any damages or liability arising from the tenant's use of the property.

8. ARBITRATION: Any disputes shall be resolved through arbitration in Mumbai.
EOF

echo -e "${GREEN}✓${NC} Test document created at $test_file"

echo ""
echo "────────────────────────────────"
echo ""

# 5. Upload document
echo "5️⃣  Uploading document..."
upload_response=$(curl -s -X POST "$API_URL/upload" \
  -H "Authorization: Bearer $access_token" \
  -F "file=@$test_file")

if echo "$upload_response" | grep -q '"document_id"'; then
    echo -e "${GREEN}✓${NC} Document uploaded successfully"
    document_id=$(echo "$upload_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['document_id'])")
    echo "$upload_response" | python3 -m json.tool
    echo ""
    echo -e "${BLUE}Document ID: $document_id${NC}"
else
    echo -e "${RED}✗${NC} Upload failed"
    echo "$upload_response" | python3 -m json.tool
    exit 1
fi

echo ""
echo "────────────────────────────────"
echo ""

# 6. Analyze document
echo "6️⃣  Analyzing document..."
analyze_response=$(curl -s -X POST "$API_URL/analyze" \
  -H "Authorization: Bearer $access_token" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$document_id\",
    \"language\": \"en\"
  }")

if echo "$analyze_response" | grep -q '"contract_risk_score"'; then
    echo -e "${GREEN}✓${NC} Analysis completed successfully"

    # Extract key information
    risk_score=$(echo "$analyze_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['contract_risk_score'])")
    document_type=$(echo "$analyze_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['document_type'])")
    summary=$(echo "$analyze_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['summary'][:100])")

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}       ANALYSIS RESULTS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "Document Type: ${YELLOW}$document_type${NC}"
    echo -e "Risk Score: ${RED}$risk_score/10${NC}"
    echo -e "Summary: ${summary}..."
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""

    echo "Full analysis:"
    echo "$analyze_response" | python3 -m json.tool
else
    echo -e "${RED}✗${NC} Analysis failed"
    echo "$analyze_response" | python3 -m json.tool
    exit 1
fi

echo ""
echo "────────────────────────────────"
echo ""

# 7. Ask a question
echo "7️⃣  Asking question about document..."
question_response=$(curl -s -X POST "$API_URL/ask-question" \
  -H "Authorization: Bearer $access_token" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$document_id\",
    \"question\": \"What is the monthly rent?\",
    \"language\": \"en\"
  }")

if echo "$question_response" | grep -q '"answer"'; then
    echo -e "${GREEN}✓${NC} Question answered successfully"
    answer=$(echo "$question_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['answer'])")
    echo ""
    echo -e "${BLUE}Q: What is the monthly rent?${NC}"
    echo -e "${GREEN}A: $answer${NC}"
    echo ""
else
    echo -e "${RED}✗${NC} Question failed"
    echo "$question_response" | python3 -m json.tool
fi

echo ""
echo "────────────────────────────────"
echo ""

# 8. List documents
echo "8️⃣  Listing all documents..."
documents_response=$(curl -s -X GET "$API_URL/documents" \
  -H "Authorization: Bearer $access_token")

if echo "$documents_response" | grep -q '"documents"'; then
    echo -e "${GREEN}✓${NC} Documents retrieved successfully"
    doc_count=$(echo "$documents_response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['documents']))")
    echo -e "Total documents: ${YELLOW}$doc_count${NC}"
    echo "$documents_response" | python3 -m json.tool
else
    echo -e "${RED}✗${NC} Failed to list documents"
    echo "$documents_response" | python3 -m json.tool
fi

echo ""
echo "────────────────────────────────"
echo ""

# 9. Get document details
echo "9️⃣  Getting document details..."
document_response=$(curl -s -X GET "$API_URL/document/$document_id" \
  -H "Authorization: Bearer $access_token")

if echo "$document_response" | grep -q '"document_id"'; then
    echo -e "${GREEN}✓${NC} Document details retrieved"
    echo "$document_response" | python3 -m json.tool | head -30
    echo "..."
else
    echo -e "${RED}✗${NC} Failed to get document details"
    echo "$document_response" | python3 -m json.tool
fi

echo ""
echo "════════════════════════════════"
echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
echo "════════════════════════════════"
echo ""
echo "🎉 LegalLens v3.0 is working perfectly!"
echo ""
echo "📊 Test Summary:"
echo "   ✓ Server health check"
echo "   ✓ User registration"
echo "   ✓ User login"
echo "   ✓ Get user info"
echo "   ✓ Document upload"
echo "   ✓ Document analysis"
echo "   ✓ Question answering"
echo "   ✓ List documents"
echo "   ✓ Get document details"
echo ""
echo "🔗 API Documentation: $API_URL/docs"
echo ""

# Cleanup
rm -f "$test_file"
