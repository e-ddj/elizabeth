#!/bin/bash

ALB_URL="http://microservices-alb-822314501.ap-southeast-1.elb.amazonaws.com"

echo "🧪 Testing CORS on all endpoints"
echo "================================"
echo ""

# Test each service
SERVICES=(
    "job-enricher"
    "job-extractor"
    "job-matcher"
    "hcp"
)

for SERVICE in "${SERVICES[@]}"; do
    echo "Testing $SERVICE..."
    echo "-------------------"
    
    # Test OPTIONS preflight
    echo "OPTIONS request:"
    curl -s -i -X OPTIONS \
        -H "Origin: https://your-app.vercel.app" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        "$ALB_URL/api/$SERVICE/health" 2>&1 | grep -E "(HTTP/|Access-Control-)"
    
    echo ""
    
    # Test GET with Origin header
    echo "GET request with Origin:"
    curl -s -i -X GET \
        -H "Origin: https://your-app.vercel.app" \
        "$ALB_URL/api/$SERVICE/health" 2>&1 | grep -E "(HTTP/|Access-Control-|healthy)"
    
    echo -e "\n"
done

echo "📝 Summary:"
echo "If you see 'Access-Control-Allow-Origin' headers, CORS is working."
echo "If not, the deployment hasn't updated the services yet."