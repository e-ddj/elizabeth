#!/bin/bash

echo "🔍 Monitoring service deployment..."
echo ""

while true; do
    clear
    echo "=== Service Status at $(date) ==="
    echo ""
    
    aws ecs describe-services \
        --cluster microservices-cluster \
        --services job-enricher job-extractor job-matcher resume-parser \
        --region ap-southeast-1 \
        --query "services[*].{Service:serviceName,Running:runningCount,Desired:desiredCount,Status:deployments[0].rolloutState}" \
        --output table
    
    echo ""
    echo "=== Recent Events ==="
    
    for SERVICE in job-extractor job-matcher; do
        echo ""
        echo "--- $SERVICE ---"
        aws ecs describe-services \
            --cluster microservices-cluster \
            --services $SERVICE \
            --region ap-southeast-1 \
            --query 'services[0].events[0:2].[createdAt,message]' \
            --output text | head -4
    done
    
    echo ""
    echo "=== Task Failures ==="
    
    for SERVICE in job-extractor job-matcher; do
        TASK=$(aws ecs list-tasks --cluster microservices-cluster --service-name $SERVICE --desired-status STOPPED --region ap-southeast-1 --max-items 1 --query 'taskArns[0]' --output text 2>/dev/null)
        if [ "$TASK" != "None" ] && [ ! -z "$TASK" ]; then
            echo "$SERVICE: $(aws ecs describe-tasks --cluster microservices-cluster --tasks $TASK --region ap-southeast-1 --query 'tasks[0].stoppedReason' --output text 2>/dev/null)"
        fi
    done
    
    echo ""
    echo "Press Ctrl+C to stop monitoring..."
    sleep 10
done