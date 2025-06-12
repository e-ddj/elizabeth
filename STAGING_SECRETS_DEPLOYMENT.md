# Staging Environment Secrets Deployment Guide

## Overview

This guide explains how to add the required GitHub repository secrets to enable multi-environment deployment (Development, Staging, Production) for the microservices platform on AWS ECS.

## Required GitHub Repository Secrets

To enable staging environment support, you need to add the following secrets to your GitHub repository:

### Navigation to Secrets Settings
1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/elizabeth`
2. Click on the **Settings** tab
3. In the left sidebar, scroll to **Security** section
4. Click **Secrets and variables** → **Actions**

### Required Secrets to Add

#### 1. Staging Environment Supabase URL
- **Name**: `SUPABASE_URL_STAGING`
- **Value**: `https://lgaczmbobvbtuysgefwv.supabase.co`

#### 2. Staging Environment Supabase Service Role Key
- **Name**: `SUPABASE_PRIVATE_SERVICE_ROLE_KEY_STAGING`
- **Value**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxnYWN6bWJvYnZidHV5c2dlZnd2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTQ1ODY4MSwiZXhwIjoyMDY1MDM0NjgxfQ.C-kw99yevQJaZVuX28UegLrBTj0B_UR7RIN4OadJ668`

#### 3. Production Environment Supabase URL
- **Name**: `SUPABASE_URL_PROD`
- **Value**: `https://abfeebfydwvyjkbbhyec.supabase.co`

#### 4. Production Environment Supabase Service Role Key
- **Name**: `SUPABASE_PRIVATE_SERVICE_ROLE_KEY_PROD`
- **Value**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiZmVlYmZ5ZHd2eWprYmJoeWVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODE2MjM3NSwiZXhwIjoyMDYzNzM4Mzc1fQ.2FWrvChWKktaAhTF7P3Bx9olid6PW80UnxPA3rMKTqE`

#### 5. OpenAI API Key (if not already added)
- **Name**: `OPENAI_API_KEY`
- **Value**: Your OpenAI API key

## How the Deployment Works

### Environment Configuration
Once the secrets are added, the GitHub Actions workflows will automatically:

1. **Set DEFAULT_ENVIRONMENT=production** for AWS deployments
2. **Inject all environment-specific credentials** into ECS task definitions
3. **Enable header-based routing** via the `X-Environment` header
4. **Maintain backward compatibility** with existing production deployments

### Environment Selection Logic
The microservices use this priority order to determine which environment to connect to:

1. **Request Header**: Check for `X-Environment` header (`development`, `staging`, `production`)
2. **Default Environment**: Fall back to `DEFAULT_ENVIRONMENT` (set to `production` on AWS)
3. **Legacy Support**: Use original `SUPABASE_URL` and `SUPABASE_PRIVATE_SERVICE_ROLE_KEY` as final fallback

## Testing Multi-Environment Deployment

### After Secrets Are Added and Code is Pushed:

#### Test Production Environment (Default)
```bash
curl https://your-alb-domain.com/api/job-matcher/health
```

#### Test Staging Environment
```bash
curl -H "X-Environment: staging" https://your-alb-domain.com/api/job-matcher/health
```

#### Test Development Environment (if using local Supabase)
```bash
curl -H "X-Environment: development" https://your-alb-domain.com/api/job-matcher/health
```

## Deployment Process

### When You Push Changes to GitHub:

1. **GitHub Actions triggers** the deployment workflow
2. **Docker images are built** with the latest code
3. **ECS task definitions are updated** with:
   - New Docker image
   - All environment-specific secrets
   - `DEFAULT_ENVIRONMENT=production`
   - Required environment variables (Redis, Gunicorn config, etc.)
4. **ECS services are updated** with the new task definitions
5. **Services restart** with the new configuration

## Security Considerations

### Environment Isolation
- Each environment uses completely separate Supabase databases
- Invalid `X-Environment` headers default to production
- Environment-specific credentials are never logged

### Secret Management
- All sensitive credentials are stored as GitHub repository secrets
- Secrets are injected into ECS containers as environment variables
- Consider migrating to AWS Secrets Manager for enhanced security

## Monitoring

### Check Deployment Status
1. Go to your repository's **Actions** tab
2. Monitor the "Deploy to AWS ECS" workflow
3. Check CloudWatch logs for environment selection logs:
   ```
   INFO: Using environment: production
   INFO: Creating Supabase client for production environment
   ```

### Environment Usage Logs
Each service logs which environment it's connecting to:
```
INFO: Request processed for staging environment
INFO: Request processed for production environment
```

## Troubleshooting

### Common Issues

#### Missing Secrets Error
```
Error: Supabase credentials not found for staging environment
```
**Solution**: Ensure all required secrets are added to GitHub repository

#### Invalid Environment Header
```
INFO: Using environment: production
```
**Solution**: Valid values are `development`, `staging`, `production` (case-sensitive)

#### Deployment Failures
- Check the Actions tab for workflow errors
- Verify AWS credentials are still valid
- Ensure ECS cluster and services exist

## Next Steps

1. **Add the required secrets** to your GitHub repository
2. **Push your latest changes** to trigger deployment
3. **Monitor the deployment** in the Actions tab
4. **Test the endpoints** with different `X-Environment` headers
5. **Check CloudWatch logs** for environment selection confirmation

The platform is now ready for multi-environment deployment with staging and production database isolation!