# GitHub Actions Deployment Setup

This directory contains GitHub Actions workflows for automatic deployment to AWS ECS.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

### AWS Credentials (Required)
- `AWS_ACCESS_KEY_ID`: Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key

### Optional
- `SLACK_WEBHOOK_URL`: Slack webhook URL for deployment notifications

## How to Set Up

1. Go to your GitHub repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add each required secret

### Getting AWS Credentials

1. Create an IAM user in AWS with the following permissions:
   - ECS full access
   - ECR full access
   - IAM pass role (for ECS task execution)

2. Or use this minimal policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:BatchGetImage",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```

## Workflow Triggers

The deployment workflow runs:
- Automatically on every push to the `main` branch
- Manually via GitHub Actions UI (workflow_dispatch)

## What the Workflow Does

1. Checks out the code
2. Configures AWS credentials
3. Logs into Amazon ECR
4. Builds all service Docker images (linux/amd64 platform)
5. Pushes images to ECR with commit SHA and 'latest' tags
6. Updates ECS task definitions with new images
7. Updates ECS services to use new task definitions
8. Waits for services to stabilize
9. Sends Slack notification (if configured)

## Monitoring Deployments

- Check the Actions tab in GitHub to see deployment status
- Each deployment is tagged with the commit SHA
- Services are updated with zero-downtime rolling deployments
- Check AWS ECS console for detailed service status

## Troubleshooting

If deployment fails:
1. Check GitHub Actions logs for error messages
2. Verify AWS credentials are correct
3. Ensure ECR repositories exist for all services
4. Check ECS task definitions have proper IAM roles
5. Verify ECS services have enough capacity for rolling updates