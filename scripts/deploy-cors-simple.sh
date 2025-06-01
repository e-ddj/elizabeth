#!/bin/bash

# Simple script to force deployment of CORS fixes

set -e

REGION="ap-southeast-1"
CLUSTER="microservices-cluster"
SERVICES=("job-enricher" "job-extractor" "resume-parser")

echo "🚀 Deploying CORS fixes..."
echo "========================="

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "Updating $SERVICE..."
    
    # Force new deployment with latest image
    aws ecs update-service \
        --cluster $CLUSTER \
        --service $SERVICE \
        --force-new-deployment \
        --region $REGION \
        --query 'service.serviceName' \
        --output text
    
    echo "✅ $SERVICE deployment started"
done

echo ""
echo "⏳ Services are updating (2-3 minutes)..."
echo ""
echo "Monitor status with:"
echo "./scripts/check-service-status.sh"
echo ""
echo "Test CORS after deployment:"
echo "curl -i -X OPTIONS -H 'Origin: https://your-app.vercel.app' http://microservices-alb-822314501.ap-southeast-1.elb.amazonaws.com/api/job-extractor/extract"