#!/bin/bash

# Complete fix script to update service ports and target groups

set -e

echo "Fixing port configurations for job-extractor and job-matcher..."

# First, update the target groups to use the correct ports
echo "Updating target groups..."

# Get target group ARNs
JOB_EXTRACTOR_TG=$(aws elbv2 describe-target-groups --names job-extractor-tg --region ap-southeast-1 --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || echo "")
JOB_MATCHER_TG=$(aws elbv2 describe-target-groups --names job-matcher-tg --region ap-southeast-1 --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || echo "")

if [ ! -z "$JOB_EXTRACTOR_TG" ]; then
  echo "Updating job-extractor target group to port 5001..."
  aws elbv2 modify-target-group --target-group-arn $JOB_EXTRACTOR_TG --port 5001 --region ap-southeast-1
fi

if [ ! -z "$JOB_MATCHER_TG" ]; then
  echo "Updating job-matcher target group to port 5001..."
  aws elbv2 modify-target-group --target-group-arn $JOB_MATCHER_TG --port 5001 --region ap-southeast-1
fi

# Now update the task definitions
echo "Updating task definitions..."

# Update job-extractor
echo "Creating new task definition for job-extractor..."
aws ecs describe-task-definition --task-definition job-extractor --region ap-southeast-1 --query 'taskDefinition' > task-def-job-extractor.json

jq '.containerDefinitions[0].portMappings[0].containerPort = 5001 |
    .containerDefinitions[0].portMappings[0].hostPort = 5001 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5001/health || exit 1"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' \
    task-def-job-extractor.json > new-task-def-job-extractor.json

JOB_EXTRACTOR_TASK_DEF=$(aws ecs register-task-definition \
  --cli-input-json file://new-task-def-job-extractor.json \
  --region ap-southeast-1 \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "✅ job-extractor task definition created: $JOB_EXTRACTOR_TASK_DEF"

# Update job-matcher
echo "Creating new task definition for job-matcher..."
aws ecs describe-task-definition --task-definition job-matcher --region ap-southeast-1 --query 'taskDefinition' > task-def-job-matcher.json

jq '.containerDefinitions[0].portMappings[0].containerPort = 5001 |
    .containerDefinitions[0].portMappings[0].hostPort = 5001 |
    .containerDefinitions[0].healthCheck.command = ["CMD-SHELL", "curl -f http://localhost:5001/health || exit 1"] |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' \
    task-def-job-matcher.json > new-task-def-job-matcher.json

JOB_MATCHER_TASK_DEF=$(aws ecs register-task-definition \
  --cli-input-json file://new-task-def-job-matcher.json \
  --region ap-southeast-1 \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "✅ job-matcher task definition created: $JOB_MATCHER_TASK_DEF"

# Stop current tasks to force new deployments
echo "Stopping current tasks to force new deployments..."

# Stop job-extractor tasks
JOB_EXTRACTOR_TASKS=$(aws ecs list-tasks --cluster microservices-cluster --service-name job-extractor --region ap-southeast-1 --query 'taskArns[]' --output text)
if [ ! -z "$JOB_EXTRACTOR_TASKS" ]; then
  for TASK in $JOB_EXTRACTOR_TASKS; do
    echo "Stopping job-extractor task: $TASK"
    aws ecs stop-task --cluster microservices-cluster --task $TASK --region ap-southeast-1 >/dev/null
  done
fi

# Stop job-matcher tasks
JOB_MATCHER_TASKS=$(aws ecs list-tasks --cluster microservices-cluster --service-name job-matcher --region ap-southeast-1 --query 'taskArns[]' --output text)
if [ ! -z "$JOB_MATCHER_TASKS" ]; then
  for TASK in $JOB_MATCHER_TASKS; do
    echo "Stopping job-matcher task: $TASK"
    aws ecs stop-task --cluster microservices-cluster --task $TASK --region ap-southeast-1 >/dev/null
  done
fi

# Update services with new task definitions
echo "Updating services with new task definitions..."

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-extractor \
  --task-definition $JOB_EXTRACTOR_TASK_DEF \
  --force-new-deployment \
  --region ap-southeast-1 >/dev/null

echo "✅ job-extractor service updated"

aws ecs update-service \
  --cluster microservices-cluster \
  --service job-matcher \
  --task-definition $JOB_MATCHER_TASK_DEF \
  --force-new-deployment \
  --region ap-southeast-1 >/dev/null

echo "✅ job-matcher service updated"

# Clean up
rm -f task-def-*.json new-task-def-*.json

echo ""
echo "🎉 Port configurations fixed!"
echo ""
echo "Services are now restarting with the correct port configurations."
echo "This should resolve the health check failures."
echo ""
echo "Monitor deployment progress with:"
echo "aws ecs describe-services --cluster microservices-cluster --services job-extractor job-matcher --region ap-southeast-1 --query 'services[*].{Service:serviceName,RunningCount:runningCount,DesiredCount:desiredCount,Deployments:deployments[0].rolloutState}' --output table"