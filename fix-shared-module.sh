#!/bin/bash

# Quick fix to copy shared module into services that need it

set -e

echo "🔧 Fixing shared module issue in services..."
echo ""

# Copy shared directory to services that use it
for SERVICE in job-extractor job-matcher resume-parser; do
    echo "Copying shared directory to $SERVICE..."
    cp -r /Users/eee/www/elizabeth/shared /Users/eee/www/elizabeth/services/$SERVICE/
done

echo ""
echo "✅ Shared module copied to services!"
echo ""
echo "Now you need to rebuild and push the Docker images with the shared module included."
echo ""
echo "Run these commands:"
echo ""
echo "cd /Users/eee/www/elizabeth"
echo ""
echo "# Build and push job-extractor"
echo "docker build -t 558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices/job-extractor:latest -f services/job-extractor/dockerfile services/job-extractor"
echo "docker push 558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices/job-extractor:latest"
echo ""
echo "# Build and push job-matcher"
echo "docker build -t 558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices/job-matcher:latest -f services/job-matcher/dockerfile services/job-matcher"
echo "docker push 558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices/job-matcher:latest"
echo ""
echo "# Build and push resume-parser"
echo "docker build -t 558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices/resume-parser:latest -f services/resume-parser/dockerfile services/resume-parser"
echo "docker push 558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices/resume-parser:latest"
echo ""
echo "Then force new deployments to use the updated images."