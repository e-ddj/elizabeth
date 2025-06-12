#!/bin/bash

# Quick fix script to update service ports for job-extractor and job-matcher

set -e

echo "Fixing port configurations for job-extractor and job-matcher..."

# Update job-extractor
echo "Updating job-extractor to use port 5001..."
aws ecs describe-task-definition --task-definition job-extractor --region ap-southeast-1 --query 'taskDefinition' > task-def-job-extractor.json

jq '.containerDefinitions[0].portMappings[0].containerPort = 5001 |
    .containerDefinitions[0].portMappings[0].hostPort = 5001 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5001/health || exit 1"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' \
    task-def-job-extractor.json > new-task-def-job-extractor.json

NEW_TASK_DEF=$(aws ecs register-task-definition \
  --cli-input-json file://new-task-def-job-extractor.json \
  --region ap-southeast-1 \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-extractor \
  --task-definition $NEW_TASK_DEF \
  --force-new-deployment \
  --region ap-southeast-1

echo "✅ job-extractor updated to use port 5001"

# Update job-matcher
echo "Updating job-matcher to use port 5001..."
aws ecs describe-task-definition --task-definition job-matcher --region ap-southeast-1 --query 'taskDefinition' > task-def-job-matcher.json

jq '.containerDefinitions[0].portMappings[0].containerPort = 5001 |
    .containerDefinitions[0].portMappings[0].hostPort = 5001 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5001/health || exit 1"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' \
    task-def-job-matcher.json > new-task-def-job-matcher.json

NEW_TASK_DEF=$(aws ecs register-task-definition \
  --cli-input-json file://new-task-def-job-matcher.json \
  --region ap-southeast-1 \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-matcher \
  --task-definition $NEW_TASK_DEF \
  --force-new-deployment \
  --region ap-southeast-1

echo "✅ job-matcher updated to use port 5001"

# Clean up
rm -f task-def-*.json new-task-def-*.json

echo "🎉 Port configurations fixed! Services should stabilize within a few minutes."
echo "Monitor deployment progress with:"
echo "aws ecs describe-services --cluster microservices-cluster --services job-extractor job-matcher --region ap-southeast-1"