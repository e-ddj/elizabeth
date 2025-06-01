#!/bin/bash

# Direct deployment script - bypasses GitHub Actions

set -e

REGION="ap-southeast-1"
ECR_REGISTRY="558379060332.dkr.ecr.ap-southeast-1.amazonaws.com"
CLUSTER="microservices-cluster"

echo "🚀 Direct Deployment - Pushing CORS fixes"
echo "========================================="

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Services to update
SERVICES=("job-enricher" "job-extractor" "resume-parser" "job-matcher")

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "📦 Deploying $SERVICE..."
    
    # Build with current code
    docker build \
        --platform linux/amd64 \
        -t $ECR_REGISTRY/microservices/$SERVICE:latest \
        -t $ECR_REGISTRY/microservices/$SERVICE:cors-fixed \
        -f services/$SERVICE/dockerfile \
        services/$SERVICE
    
    # Push to ECR
    echo "Pushing image..."
    docker push $ECR_REGISTRY/microservices/$SERVICE:latest
    docker push $ECR_REGISTRY/microservices/$SERVICE:cors-fixed
    
    # Force service update
    echo "Updating ECS service..."
    aws ecs update-service \
        --cluster $CLUSTER \
        --service $SERVICE \
        --force-new-deployment \
        --region $REGION \
        --output text > /dev/null
    
    echo "✅ $SERVICE deployed"
done

echo ""
echo "🎉 All services deployed with CORS fixes!"
echo ""
echo "Wait 2-3 minutes for services to update, then test:"
echo "./test-cors-endpoints.sh"