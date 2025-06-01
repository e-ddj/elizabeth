#!/bin/bash

# Script to deploy CORS fixes to specific services
# This is a quick deployment for the CORS updates

set -e

REGION="ap-southeast-1"
CLUSTER="microservices-cluster"
ECR_REGISTRY="558379060332.dkr.ecr.ap-southeast-1.amazonaws.com"

echo "🔧 Deploying CORS fixes to services..."
echo "====================================="

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Services that were updated
SERVICES=("job-enricher" "job-extractor" "resume-parser")

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "📦 Building and deploying $SERVICE..."
    
    # Build the image
    echo "Building Docker image..."
    docker build \
        --platform linux/amd64 \
        --build-arg SERVICE_NAME=$SERVICE \
        -t $ECR_REGISTRY/$SERVICE:latest \
        -t $ECR_REGISTRY/$SERVICE:cors-fix \
        -f services/$SERVICE/dockerfile \
        services/$SERVICE
    
    # Push the image
    echo "Pushing to ECR..."
    docker push $ECR_REGISTRY/$SERVICE:latest
    docker push $ECR_REGISTRY/$SERVICE:cors-fix
    
    # Update the service to use the new image
    echo "Updating ECS service..."
    aws ecs update-service \
        --cluster $CLUSTER \
        --service $SERVICE \
        --force-new-deployment \
        --region $REGION \
        --output text > /dev/null
    
    echo "✅ $SERVICE updated with CORS fix"
done

echo ""
echo "⏳ Waiting for services to stabilize..."

for SERVICE in "${SERVICES[@]}"; do
    echo -n "   Waiting for $SERVICE... "
    aws ecs wait services-stable \
        --cluster $CLUSTER \
        --services $SERVICE \
        --region $REGION 2>/dev/null && echo "✅" || echo "⚠️  (timeout, but may still be updating)"
done

echo ""
echo "🎉 CORS fixes deployed!"
echo ""
echo "Test CORS with:"
echo "curl -H 'Origin: https://example.com' -I http://microservices-alb-822314501.ap-southeast-1.elb.amazonaws.com/api/job-extractor/health"