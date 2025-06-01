#!/bin/bash

# Script to wake up (start) ECS services
# Usage: ./scripts/wake-services.sh [task-count]

set -e

CLUSTER="microservices-cluster"
REGION="ap-southeast-1"
SERVICES=("job-enricher" "job-extractor" "job-matcher" "resume-parser")
TASK_COUNT="${1:-1}"  # Default to 1 task per service for minimal cost

echo "☀️  Waking up ECS services..."
echo "============================"
echo "Task count per service: $TASK_COUNT"
echo ""

for SERVICE in "${SERVICES[@]}"; do
    echo "Starting $SERVICE with $TASK_COUNT task(s)..."
    
    # Scale service to desired count
    aws ecs update-service \
        --cluster $CLUSTER \
        --service $SERVICE \
        --desired-count $TASK_COUNT \
        --region $REGION \
        --output text > /dev/null
    
    echo "✅ $SERVICE scaling to $TASK_COUNT task(s)"
done

echo ""
echo "⏳ Waiting for services to stabilize (this may take a few minutes)..."

# Wait for all services to stabilize
for SERVICE in "${SERVICES[@]}"; do
    echo -n "   Waiting for $SERVICE... "
    
    aws ecs wait services-stable \
        --cluster $CLUSTER \
        --services $SERVICE \
        --region $REGION 2>/dev/null && echo "✅" || echo "⚠️  (timeout, but may still be starting)"
done

echo ""
echo "🚀 Services are starting up!"
echo ""
echo "💰 Estimated cost:"
echo "   - Per service: ~$0.012/hour ($8.64/month)"
echo "   - Total (4 services): ~$0.048/hour ($34.56/month)"
echo ""
echo "💡 Remember to hibernate services when not in use:"
echo "   ./scripts/hibernate-services.sh"