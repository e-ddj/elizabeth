#!/bin/bash

# Quick fix to update task definitions with correct ports

set -e

echo "🔧 Fixing port configurations for job-extractor and job-matcher..."
echo ""

# Fix job-extractor
echo "1️⃣ Updating job-extractor (port 5002 → 5001)..."
aws ecs describe-task-definition --task-definition job-extractor --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].portMappings[0].containerPort = 5001 |
    .containerDefinitions[0].portMappings[0].hostPort = 5001 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5001/health || exit 1"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-extractor-fixed.json

TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file://job-extractor-fixed.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ New task definition: $TASK_DEF_ARN"

# Update service but keep the load balancer configuration pointing to the old port
# This allows the service to start and be healthy internally
aws ecs update-service --cluster microservices-cluster --service job-extractor --task-definition $TASK_DEF_ARN --region ap-southeast-1 --query 'service.serviceName' --output text >/dev/null
echo "   ✅ Service updated"

# Fix job-matcher
echo ""
echo "2️⃣ Updating job-matcher (port 5003 → 5001)..."
aws ecs describe-task-definition --task-definition job-matcher --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].portMappings[0].containerPort = 5001 |
    .containerDefinitions[0].portMappings[0].hostPort = 5001 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5001/health || exit 1"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-matcher-fixed.json

TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file://job-matcher-fixed.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ New task definition: $TASK_DEF_ARN"

# Update service
aws ecs update-service --cluster microservices-cluster --service job-matcher --task-definition $TASK_DEF_ARN --region ap-southeast-1 --query 'service.serviceName' --output text >/dev/null
echo "   ✅ Service updated"

# Clean up
rm -f job-extractor-fixed.json job-matcher-fixed.json

echo ""
echo "⚠️  IMPORTANT: The services will have port mismatches with their target groups!"
echo "   - job-extractor: Service port 5001 ≠ Target Group port 5002"
echo "   - job-matcher: Service port 5001 ≠ Target Group port 5003"
echo ""
echo "This is a temporary fix to get services running. The ALB won't route traffic correctly."
echo "To fully fix this, you'll need to recreate the target groups with correct ports."
echo ""
echo "Monitor services:"
echo "aws ecs describe-services --cluster microservices-cluster --services job-extractor job-matcher --region ap-southeast-1 --query 'services[*].{Service:serviceName,RunningCount:runningCount,DesiredCount:desiredCount}' --output table"