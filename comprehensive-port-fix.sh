#!/bin/bash

# Comprehensive fix to align all port configurations

set -e

echo "🔧 Comprehensive port alignment fix..."
echo ""

# Stop the problematic deployments first
echo "⏸️  Canceling stuck deployments..."
aws ecs update-service --cluster microservices-cluster --service job-extractor --desired-count 0 --region ap-southeast-1 >/dev/null 2>&1 || true
aws ecs update-service --cluster microservices-cluster --service job-matcher --desired-count 0 --region ap-southeast-1 >/dev/null 2>&1 || true
sleep 5

# Fix job-extractor to use port 5002 everywhere
echo ""
echo "1️⃣ Fixing job-extractor (align to port 5002)..."
aws ecs describe-task-definition --task-definition job-extractor --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].portMappings[0].containerPort = 5002 |
    .containerDefinitions[0].portMappings[0].hostPort = 5002 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5002/health || exit 1"] |
    .containerDefinitions[0].environment = ((.containerDefinitions[0].environment // []) | map(select(.name != "PORT")) + [{"name": "PORT", "value": "5002"}]) |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-extractor-complete.json

EXTRACTOR_TASK_DEF=$(aws ecs register-task-definition --cli-input-json file://job-extractor-complete.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ Task definition created: ${EXTRACTOR_TASK_DEF##*/}"

# Fix job-matcher to use port 5003 everywhere  
echo ""
echo "2️⃣ Fixing job-matcher (align to port 5003)..."
aws ecs describe-task-definition --task-definition job-matcher --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].portMappings[0].containerPort = 5003 |
    .containerDefinitions[0].portMappings[0].hostPort = 5003 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5003/health || exit 1"] |
    .containerDefinitions[0].environment = ((.containerDefinitions[0].environment // []) | map(select(.name != "PORT")) + [{"name": "PORT", "value": "5003"}]) |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-matcher-complete.json

MATCHER_TASK_DEF=$(aws ecs register-task-definition --cli-input-json file://job-matcher-complete.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ Task definition created: ${MATCHER_TASK_DEF##*/}"

# Update services with new task definitions and restart
echo ""
echo "🚀 Restarting services with correct configurations..."

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-extractor \
  --task-definition $EXTRACTOR_TASK_DEF \
  --desired-count 1 \
  --force-new-deployment \
  --region ap-southeast-1 >/dev/null

echo "   ✅ job-extractor service updated"

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-matcher \
  --task-definition $MATCHER_TASK_DEF \
  --desired-count 1 \
  --force-new-deployment \
  --region ap-southeast-1 >/dev/null

echo "   ✅ job-matcher service updated"

# Clean up
rm -f job-extractor-complete.json job-matcher-complete.json

echo ""
echo "✅ All port configurations aligned!"
echo ""
echo "Services are configured as:"
echo "  - job-enricher: port 5001 (no change needed)"
echo "  - job-extractor: port 5002 (PORT env var + container port + health check)"
echo "  - job-matcher: port 5003 (PORT env var + container port + health check)"
echo "  - resume-parser: port 5004 (no change needed)"
echo ""
echo "These match the nginx upstream configuration and ALB target groups."
echo ""
echo "📊 Monitor deployment status:"
echo "watch -n 5 'aws ecs describe-services --cluster microservices-cluster --services job-extractor job-matcher --region ap-southeast-1 --query \"services[*].{Service:serviceName,Running:runningCount,Desired:desiredCount,Status:deployments[0].rolloutState}\" --output table'"