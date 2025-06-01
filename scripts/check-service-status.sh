#!/bin/bash

# Script to check the status and cost of ECS services
# Usage: ./scripts/check-service-status.sh

set -e

CLUSTER="microservices-cluster"
REGION="ap-southeast-1"
SERVICES=("job-enricher" "job-extractor" "job-matcher" "resume-parser")

echo "📊 ECS Service Status & Cost Report"
echo "==================================="
echo ""

TOTAL_TASKS=0
TOTAL_COST_HOUR=0

for SERVICE in "${SERVICES[@]}"; do
    # Get service details
    SERVICE_INFO=$(aws ecs describe-services \
        --cluster $CLUSTER \
        --services $SERVICE \
        --region $REGION \
        --query 'services[0].[desiredCount,runningCount,pendingCount]' \
        --output text 2>/dev/null || echo "0 0 0")
    
    read DESIRED RUNNING PENDING <<< "$SERVICE_INFO"
    
    # Calculate cost (Fargate pricing for 0.25 vCPU, 0.5 GB RAM)
    # vCPU: $0.04048/hour × 0.25 = $0.01012/hour
    # Memory: $0.004445/GB/hour × 0.5 = $0.002223/hour
    # Total per task: ~$0.012/hour
    COST_PER_HOUR=$(echo "scale=3; $RUNNING * 0.012" | bc)
    COST_PER_MONTH=$(echo "scale=2; $COST_PER_HOUR * 720" | bc)
    
    # Status emoji
    if [ "$DESIRED" = "0" ]; then
        STATUS="💤 Hibernating"
    elif [ "$RUNNING" = "$DESIRED" ]; then
        STATUS="✅ Running"
    elif [ "$PENDING" -gt "0" ]; then
        STATUS="🔄 Starting"
    else
        STATUS="⚠️  Issues"
    fi
    
    printf "%-20s %s\n" "$SERVICE:" "$STATUS"
    printf "  Tasks: %d/%d (running/desired)\n" "$RUNNING" "$DESIRED"
    
    if [ "$RUNNING" -gt "0" ]; then
        printf "  Cost: \$%.3f/hour (\$%.2f/month)\n" "$COST_PER_HOUR" "$COST_PER_MONTH"
    else
        printf "  Cost: \$0 (hibernating)\n"
    fi
    echo ""
    
    TOTAL_TASKS=$((TOTAL_TASKS + RUNNING))
    TOTAL_COST_HOUR=$(echo "scale=3; $TOTAL_COST_HOUR + $COST_PER_HOUR" | bc)
done

TOTAL_COST_MONTH=$(echo "scale=2; $TOTAL_COST_HOUR * 720" | bc)

echo "==================================="
echo "💰 Total Cost Summary:"
echo "  Running tasks: $TOTAL_TASKS"
echo "  Hourly cost: \$$TOTAL_COST_HOUR"
echo "  Monthly cost: \$$TOTAL_COST_MONTH"
echo ""

if [ "$TOTAL_TASKS" = "0" ]; then
    echo "🎉 All services hibernating - No compute costs!"
    echo "   Note: You may still have costs for:"
    echo "   - Load Balancer: ~\$18/month"
    echo "   - ElastiCache Redis: ~\$12/month"
    echo "   - Data transfer & storage"
else
    echo "💡 To save costs, hibernate services when not in use:"
    echo "   ./scripts/hibernate-services.sh"
fi