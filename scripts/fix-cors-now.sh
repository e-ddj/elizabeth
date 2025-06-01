#!/bin/bash

# Quick fix to deploy CORS changes to the correct ECR repository path

set -e

REGION="ap-southeast-1"
ECR_REGISTRY="558379060332.dkr.ecr.ap-southeast-1.amazonaws.com"
SERVICES=("job-enricher" "job-extractor" "resume-parser")

echo "🚨 Emergency CORS Fix Deployment"
echo "================================"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "📦 Fixing $SERVICE..."
    
    # Build the image with CORS fix
    echo "Building image..."
    docker build \
        --platform linux/amd64 \
        --build-arg SERVICE_NAME=$SERVICE \
        -t $ECR_REGISTRY/microservices/$SERVICE:latest \
        -t $ECR_REGISTRY/microservices/$SERVICE:cors-fix-$(date +%s) \
        -f services/$SERVICE/dockerfile \
        services/$SERVICE
    
    # Push to ECR
    echo "Pushing to ECR..."
    docker push $ECR_REGISTRY/microservices/$SERVICE:latest
    
    # Get current task definition and update it
    echo "Updating task definition..."
    TASK_DEF=$(aws ecs describe-task-definition --task-definition $SERVICE --region $REGION --query taskDefinition)
    
    # Update the image in task definition
    NEW_TASK_DEF=$(echo $TASK_DEF | jq \
        --arg IMAGE "$ECR_REGISTRY/microservices/$SERVICE:latest" \
        '.containerDefinitions[0].image = $IMAGE' | \
        jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')
    
    # Register new task definition
    NEW_REVISION=$(aws ecs register-task-definition --cli-input-json "$NEW_TASK_DEF" --region $REGION --query 'taskDefinition.revision' --output text)
    
    # Update service with new task definition
    echo "Updating ECS service..."
    aws ecs update-service \
        --cluster microservices-cluster \
        --service $SERVICE \
        --task-definition ${SERVICE}:${NEW_REVISION} \
        --force-new-deployment \
        --region $REGION \
        --output text > /dev/null
    
    echo "✅ $SERVICE updated with CORS fix (revision $NEW_REVISION)"
done

echo ""
echo "⏳ Services are updating. Wait 2-3 minutes then test:"
echo ""
echo "curl -i -X OPTIONS \\"
echo "  -H 'Origin: https://your-app.vercel.app' \\"
echo "  -H 'Access-Control-Request-Method: POST' \\"
echo "  http://microservices-alb-822314501.ap-southeast-1.elb.amazonaws.com/api/job-extractor/extract"
echo ""
echo "You should see Access-Control-Allow-Origin headers in the response."