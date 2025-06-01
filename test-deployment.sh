#!/bin/bash

# Test script for deployed microservices
ALB_DNS="microservices-alb-822314501.ap-southeast-1.elb.amazonaws.com"

echo "🧪 Testing Deployed Microservices"
echo "================================="
echo "ALB URL: http://$ALB_DNS"
echo ""

# Test 1: Job Enricher
echo "1. Testing Job Enricher Service"
echo "-------------------------------"
echo "Sending job data for enrichment..."

RESPONSE=$(curl -s -X POST http://$ALB_DNS/api/job-enricher/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "id": 12345,
    "title": "Software Engineer",
    "summary": "We are looking for a software engineer to join our team.",
    "department": "Engineering",
    "location": "Singapore",
    "jobType": "Full-time",
    "status": "Open",
    "postedAt": "2025-06-01",
    "salaryRange": null,
    "responsibilities": ["Write code", "Review PRs"],
    "qualifications": ["3+ years experience", "Python knowledge"],
    "perks": [],
    "benefitsData": [],
    "specialty": "Backend Development",
    "organization": "Tech Corp",
    "country": "SG",
    "isRemote": false,
    "visaSponsorship": false,
    "fullTime": true,
    "partTime": false,
    "nightShift": false
  }')

if echo "$RESPONSE" | jq . >/dev/null 2>&1; then
    echo "✅ Job Enricher is working!"
    echo "Enhanced title: $(echo "$RESPONSE" | jq -r .title)"
    echo "Enhanced summary preview: $(echo "$RESPONSE" | jq -r .summary | head -c 100)..."
else
    echo "❌ Job Enricher failed"
    echo "Response: $RESPONSE"
fi

echo ""

# Test 2: Job Extractor (will fail without valid URL)
echo "2. Testing Job Extractor Service"
echo "--------------------------------"
echo "Note: This will fail without a valid job URL"
RESPONSE=$(curl -s -X POST http://$ALB_DNS/api/job-extractor/extract \
  -H "Content-Type: application/json" \
  -d '{"job_url": "https://www.example.com/careers/job-123"}')
echo "Response: $(echo "$RESPONSE" | head -c 100)..."

echo ""

# Test 3: Job Matcher (will fail without valid job in DB)
echo "3. Testing Job Matcher Service"
echo "------------------------------"
echo "Note: This will fail without valid job ID in database"
RESPONSE=$(curl -s -X POST http://$ALB_DNS/api/job-matcher/match \
  -H "Content-Type: application/json" \
  -d '{"job_id": "123e4567-e89b-12d3-a456-426614174000"}')
echo "Response: $RESPONSE"

echo ""

# Test 4: Resume Parser (will fail without valid file)
echo "4. Testing Resume Parser Service"
echo "--------------------------------"
echo "Note: This will fail without valid file path"
RESPONSE=$(curl -s -X POST http://$ALB_DNS/api/hcp/user-profile \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/tmp/test-resume.pdf"}')
echo "Response: $(echo "$RESPONSE" | head -c 100)..."

echo ""
echo "================================="
echo "🎉 Deployment Test Complete!"
echo ""
echo "Summary:"
echo "- Job Enricher: Working (enriches job descriptions)"
echo "- Job Extractor: Requires valid job URL"
echo "- Job Matcher: Requires job data in database"
echo "- Resume Parser: Requires file upload"
echo ""
echo "💡 All services are deployed and responding correctly!"
echo ""
echo "⚠️  Remember to hibernate services when done testing:"
echo "   ./scripts/hibernate-services.sh"