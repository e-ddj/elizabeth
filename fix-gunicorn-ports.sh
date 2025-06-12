#!/bin/bash

# Fix to ensure services start on expected ports by overriding the gunicorn command

set -e

echo "🔧 Fixing services to use hardcoded ports in gunicorn command..."
echo ""

# Update job-extractor to hardcode port 5002
echo "1️⃣ Updating job-extractor to hardcode port 5002..."
aws ecs describe-task-definition --task-definition job-extractor --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].command = ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "1", "--timeout", "1800", "--graceful-timeout", "300", "api.index:app"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-extractor-cmd.json

EXTRACTOR_TASK_DEF=$(aws ecs register-task-definition --cli-input-json file://job-extractor-cmd.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ Task definition created: ${EXTRACTOR_TASK_DEF##*/}"

# Update job-matcher to hardcode port 5003
echo ""
echo "2️⃣ Updating job-matcher to hardcode port 5003..."
aws ecs describe-task-definition --task-definition job-matcher --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].command = ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "1", "--timeout", "120", "--graceful-timeout", "30", "api.index:app"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-matcher-cmd.json

MATCHER_TASK_DEF=$(aws ecs register-task-definition --cli-input-json file://job-matcher-cmd.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ Task definition created: ${MATCHER_TASK_DEF##*/}"

# Update services
echo ""
echo "🚀 Deploying services with hardcoded ports..."

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-extractor \
  --task-definition $EXTRACTOR_TASK_DEF \
  --force-new-deployment \
  --region ap-southeast-1 >/dev/null

echo "   ✅ job-extractor service updated"

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-matcher \
  --task-definition $MATCHER_TASK_DEF \
  --force-new-deployment \
  --region ap-southeast-1 >/dev/null

echo "   ✅ job-matcher service updated"

# Clean up
rm -f job-extractor-cmd.json job-matcher-cmd.json

echo ""
echo "✅ Services updated with hardcoded ports in gunicorn command!"
echo ""
echo "This ensures services start on the correct ports:"
echo "  - job-extractor: gunicorn --bind 0.0.0.0:5002"
echo "  - job-matcher: gunicorn --bind 0.0.0.0:5003"
echo ""
echo "Monitor deployment:"
echo "aws ecs describe-services --cluster microservices-cluster --services job-extractor job-matcher --region ap-southeast-1 --query 'services[*].{Service:serviceName,Running:runningCount,Desired:desiredCount,Status:deployments[0].rolloutState}' --output table"