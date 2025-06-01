#!/bin/bash

# Test script for the user-to-jobs matching endpoint
# Usage: ./test_user_match_curl.sh [user_id]

# Configuration
BASE_URL="${BASE_URL:-http://localhost:5004}"
USER_ID="${1:-123e4567-e89b-12d3-a456-426614174000}"

echo "Testing User-to-Jobs Matching Endpoint"
echo "======================================"
echo "Base URL: $BASE_URL"
echo "User ID: $USER_ID"
echo ""

# Test the endpoint
echo "Sending request..."
curl -X POST "$BASE_URL/api/job-matcher/match-user" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"overwrite_existing_matches\": false
  }" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -v

echo ""
echo "Done. Check the 'match' table in Supabase for results."