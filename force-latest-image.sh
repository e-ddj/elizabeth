#!/bin/bash

# Force ECS to use the :latest tag we just pushed

set -e

REGION="ap-southeast-1"
CLUSTER="microservices-cluster"
ECR_BASE="558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices"

SERVICES=("job-enricher" "job-extractor" "resume-parser" "job-matcher")

echo "🔧 Forcing services to use :latest images with CORS"
echo "=================================================="

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "Updating $SERVICE to use :latest image..."
    
    # Get current task definition
    TASK_DEF=$(aws ecs describe-task-definition --task-definition $SERVICE --region $REGION --query taskDefinition)
    
    # Update image to :latest
    NEW_TASK_DEF=$(echo $TASK_DEF | sed "s|$ECR_BASE/$SERVICE:[^\"]*|$ECR_BASE/$SERVICE:latest|g")
    
    # Remove fields that shouldn't be in new task definition
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | sed 's/"taskDefinitionArn":[^,]*,//g')
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | sed 's/"revision":[^,]*,//g')
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | sed 's/"status":[^,]*,//g')
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | sed 's/"requiresAttributes":[^]]*],//g')
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | sed 's/"compatibilities":[^]]*],//g')
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | sed 's/"registeredAt":[^,]*,//g')
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | sed 's/"registeredBy":[^,}]*//g')
    
    # Save to temp file
    echo $NEW_TASK_DEF > /tmp/task-def-$SERVICE.json
    
    # Register new task definition
    NEW_REV=$(aws ecs register-task-definition --cli-input-json file:///tmp/task-def-$SERVICE.json --region $REGION --query 'taskDefinition.revision' --output text)
    
    echo "New task definition revision: $NEW_REV"
    
    # Update service to use new task definition
    aws ecs update-service \
        --cluster $CLUSTER \
        --service $SERVICE \
        --task-definition ${SERVICE}:${NEW_REV} \
        --force-new-deployment \
        --region $REGION \
        --query 'service.serviceName' \
        --output text
    
    echo "✅ $SERVICE updated to use :latest image"
done

echo ""
echo "🎉 All services updated!"
echo "Wait 2-3 minutes then test CORS again."