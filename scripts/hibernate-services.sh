#!/bin/bash

# Script to hibernate (stop) all ECS services to save costs
# Usage: ./scripts/hibernate-services.sh

set -e

CLUSTER="microservices-cluster"
REGION="ap-southeast-1"
SERVICES=("job-enricher" "job-extractor" "job-matcher" "resume-parser")

echo "🌙 Hibernating ECS services to save costs..."
echo "==========================================="

for SERVICE in "${SERVICES[@]}"; do
    echo "Stopping $SERVICE..."
    
    # Scale service to 0 tasks
    aws ecs update-service \
        --cluster $CLUSTER \
        --service $SERVICE \
        --desired-count 0 \
        --region $REGION \
        --output text > /dev/null
    
    echo "✅ $SERVICE scaled to 0 tasks"
done

echo ""
echo "💰 All services hibernated. Estimated savings: ~$46/month"
echo ""
echo "Services are now:"
echo "- ✅ Updated with latest code"
echo "- 💤 Not running (no costs)"
echo "- 🚀 Ready to start when needed"
echo ""
echo "To wake services, run: ./scripts/wake-services.sh"