#!/bin/bash

# Script to align service ports with what nginx expects

set -e

echo "🔧 Aligning service ports with nginx configuration..."
echo ""
echo "Nginx expects:"
echo "  - job-enricher: 5001 ✅ (already correct)"
echo "  - job-extractor: 5002"  
echo "  - job-matcher: 5003"
echo "  - resume-parser: 5004 ✅ (already correct)"
echo ""

# Update job-extractor to use port 5002
echo "1️⃣ Updating job-extractor to use port 5002..."
aws ecs describe-task-definition --task-definition job-extractor --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].environment = (.containerDefinitions[0].environment // []) + [{"name": "PORT", "value": "5002"}] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-extractor-port.json

TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file://job-extractor-port.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ New task definition created"

aws ecs update-service --cluster microservices-cluster --service job-extractor --task-definition $TASK_DEF_ARN --force-new-deployment --region ap-southeast-1 --query 'service.serviceName' --output text >/dev/null
echo "   ✅ Service updated with PORT=5002"

# Update job-matcher to use port 5003  
echo ""
echo "2️⃣ Updating job-matcher to use port 5003..."
aws ecs describe-task-definition --task-definition job-matcher --region ap-southeast-1 --query 'taskDefinition' | \
jq '.containerDefinitions[0].environment = (.containerDefinitions[0].environment // []) + [{"name": "PORT", "value": "5003"}] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > job-matcher-port.json

TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file://job-matcher-port.json --region ap-southeast-1 --query 'taskDefinition.taskDefinitionArn' --output text)
echo "   ✅ New task definition created"

aws ecs update-service --cluster microservices-cluster --service job-matcher --task-definition $TASK_DEF_ARN --force-new-deployment --region ap-southeast-1 --query 'service.serviceName' --output text >/dev/null
echo "   ✅ Service updated with PORT=5003"

# Clean up
rm -f job-extractor-port.json job-matcher-port.json

echo ""
echo "✅ Services updated to use the ports nginx expects!"
echo ""
echo "The services will now start on the correct ports:"
echo "  - job-extractor: PORT=5002 (matching target group)"
echo "  - job-matcher: PORT=5003 (matching target group)"
echo ""
echo "Monitor deployment:"
echo "aws ecs describe-services --cluster microservices-cluster --services job-extractor job-matcher --region ap-southeast-1 --query 'services[*].{Service:serviceName,RunningCount:runningCount,DesiredCount:desiredCount,Deployments:deployments[0].rolloutState}' --output table"