#!/bin/bash

# Create ECR repositories for all services

set -e

REGION="ap-southeast-1"
SERVICES=("job-enricher" "job-extractor" "job-matcher" "resume-parser")

echo "📦 Creating ECR repositories..."
echo "=============================="

for SERVICE in "${SERVICES[@]}"; do
    echo -n "Creating repository for $SERVICE... "
    
    # Create repository if it doesn't exist
    aws ecr describe-repositories --repository-names $SERVICE --region $REGION >/dev/null 2>&1 || \
    aws ecr create-repository \
        --repository-name $SERVICE \
        --region $REGION \
        --image-scanning-configuration scanOnPush=true \
        --output text >/dev/null
    
    echo "✅"
done

echo ""
echo "✅ All ECR repositories created!"