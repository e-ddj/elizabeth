# Staging Environment Implementation Guide

## Overview

This document outlines the implementation plan for adding multi-environment support (Development, Staging, Production) to our microservices platform. The approach uses header-based routing with the `X-Environment` header to dynamically select the appropriate database and configuration for each request.

## Architecture Overview

### Current State
- Single environment configuration using hardcoded environment variables
- All services connect to the same Supabase instance
- No environment isolation between development, staging, and production

### Target State
- Three distinct environments: Development, Staging, Production
- Header-based routing via `X-Environment` header
- Each environment has its own Supabase instance
- Backward compatible with existing deployments

## Implementation Approach

### 1. Environment Configuration

#### Environment Variables Structure
```bash
# Development Environment (Local Supabase)
SUPABASE_URL_DEV=http://host.docker.internal:54321
SUPABASE_PRIVATE_SERVICE_ROLE_KEY_DEV=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Staging Environment
SUPABASE_URL_STAGING=https://your-staging-project.supabase.co
SUPABASE_PRIVATE_SERVICE_ROLE_KEY_STAGING=your_staging_service_role_key

# Production Environment
SUPABASE_URL_PROD=https://your-production-project.supabase.co
SUPABASE_PRIVATE_SERVICE_ROLE_KEY_PROD=your_production_service_role_key

# Default Environment Selection
DEFAULT_ENVIRONMENT=development  # For local development
# DEFAULT_ENVIRONMENT=production  # For AWS deployment
```

### 2. Shared Environment Utility

Create `/shared/utils/environment.py`:

```python
import os
from flask import request
import logging

logger = logging.getLogger(__name__)

def get_environment_config():
    """
    Determine environment based on X-Environment header or default.
    Supports: development, staging, production
    
    Returns:
        dict: Configuration with 'url', 'key', and 'environment'
    """
    # Check request header first
    env = None
    if request:
        env = request.headers.get('X-Environment', '').lower()
    
    # Fallback to default environment
    valid_envs = ['development', 'staging', 'production']
    if not env or env not in valid_envs:
        env = os.getenv('DEFAULT_ENVIRONMENT', 'production').lower()
    
    logger.info(f"Using environment: {env}")
    
    # Environment-specific configurations
    configs = {
        'development': {
            'url': os.getenv('SUPABASE_URL_DEV', 'http://host.docker.internal:54321'),
            'key': os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY_DEV'),
            'environment': 'development'
        },
        'staging': {
            'url': os.getenv('SUPABASE_URL_STAGING'),
            'key': os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY_STAGING'),
            'environment': 'staging'
        },
        'production': {
            'url': os.getenv('SUPABASE_URL_PROD', os.getenv('SUPABASE_URL')),
            'key': os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY_PROD', 
                           os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY')),
            'environment': 'production'
        }
    }
    
    return configs.get(env, configs['production'])

def is_development():
    """Check if running in development mode"""
    config = get_environment_config()
    return config['environment'] == 'development'

def is_staging():
    """Check if running in staging mode"""
    config = get_environment_config()
    return config['environment'] == 'staging'

def is_production():
    """Check if running in production mode"""
    config = get_environment_config()
    return config['environment'] == 'production'
```

### 3. Service-Level Changes

Each microservice needs to update its Supabase client creation to use the shared environment utility.

#### Example: job-matcher Service

**Before:**
```python
def create_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_PRIVATE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_PRIVATE_SERVICE_ROLE_KEY must be set")
    
    return create_client(url, key)
```

**After:**
```python
from shared.utils.environment import get_environment_config

def create_supabase_client() -> Client:
    config = get_environment_config()
    url = config['url']
    key = config['key']
    
    if not url or not key:
        raise ValueError(f"Supabase credentials not found for {config['environment']} environment")
    
    logger.info(f"Creating Supabase client for {config['environment']} environment")
    return create_client(url, key)
```

### 4. Nginx Configuration Updates

Update `nginx/nginx.conf` to forward the `X-Environment` header to all services:

```nginx
# In each location block, add:
proxy_set_header X-Environment $http_x_environment;

# Example for job-enricher service:
location /api/job-enricher/ {
    limit_req zone=api_limit burst=20 nodelay;
    
    proxy_pass http://job_enricher/api/job-enricher/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Environment $http_x_environment;  # Add this line
    
    # ... rest of configuration
}
```

## Implementation Checklist

### Phase 1: Infrastructure Setup
- [ ] Add staging and production Supabase credentials to `.env`
- [ ] Create `/shared/utils/environment.py` utility
- [ ] Update Nginx configuration to forward `X-Environment` header
- [ ] Test header forwarding with curl commands

### Phase 2: Service Updates
Update Supabase client creation in each service:

#### job-enricher Service
- [ ] No changes needed (doesn't use Supabase, only OpenAI)

#### job-extractor Service
Files to update:
- [ ] `/services/job-extractor/utils/supabase/client.py`
- [ ] `/services/job-extractor/api/job_extractor/extract.py` (if direct client creation)

#### job-matcher Service
Files to update:
- [ ] `/services/job-matcher/utils/supabase/client.py`

#### resume-parser Service
Files to update:
- [ ] `/services/resume-parser/utils/supabase/client.py`
- [ ] `/services/resume-parser/utils/supabase/bucket.py`

### Phase 3: Testing & Validation

#### Local Testing
```bash
# Test development environment (default)
curl http://localhost:8080/api/job-matcher/health

# Test staging environment
curl -H "X-Environment: staging" http://localhost:8080/api/job-matcher/health

# Test production environment
curl -H "X-Environment: production" http://localhost:8080/api/job-matcher/health
```

#### AWS Testing
```bash
# Test staging on AWS
curl -H "X-Environment: staging" https://your-alb-domain.com/api/job-matcher/health

# Test production (default)
curl https://your-alb-domain.com/api/job-matcher/health
```

### Phase 4: Deployment
1. Deploy shared utilities first
2. Deploy Nginx configuration update
3. Deploy each service incrementally
4. Monitor logs for environment selection

## Environment-Specific Features

### Development Environment
- Uses local Supabase instance
- Verbose logging enabled
- Debug endpoints available
- Mock external services (optional)

### Staging Environment
- Uses staging Supabase with test data
- Production-like configuration
- Performance monitoring enabled
- Integration testing environment

### Production Environment
- Uses production Supabase with live data
- Optimized performance settings
- Full monitoring and alerting
- Restricted debug access

## Security Considerations

1. **Environment Isolation**: Each environment uses completely separate databases
2. **Header Validation**: Invalid environment headers default to production
3. **Credential Protection**: Environment-specific keys are never logged
4. **Access Control**: Consider adding authentication for staging/dev header usage

## Rollback Plan

If issues arise during implementation:
1. Remove `X-Environment` header checking from services
2. Services will fall back to original environment variables
3. No database changes or API contract changes to revert

## Monitoring

Add logging to track environment usage:
```python
# In each service
logger.info(f"Request processed for {config['environment']} environment")
```

Monitor for:
- Unexpected environment selections
- Missing environment configurations
- Performance differences between environments

## Future Enhancements

1. **Environment-specific rate limiting**
   - Higher limits for development
   - Standard limits for staging
   - Strict limits for production

2. **Feature flags per environment**
   - Enable experimental features in dev/staging
   - Gradual rollout to production

3. **Environment indicators in responses**
   - Add `X-Environment-Used` response header
   - Include environment in health check responses

## Conclusion

This implementation provides a clean, maintainable approach to multi-environment support with minimal code changes. The header-based routing allows for flexible testing and development while maintaining backward compatibility with existing deployments.