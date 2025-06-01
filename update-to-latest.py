#!/usr/bin/env python3
import boto3
import json

# Initialize clients
ecs = boto3.client('ecs', region_name='ap-southeast-1')
CLUSTER = 'microservices-cluster'
ECR_BASE = '558379060332.dkr.ecr.ap-southeast-1.amazonaws.com/microservices'

services = ['job-enricher', 'job-extractor', 'resume-parser', 'job-matcher']

print("🔧 Updating ECS services to use :latest images")
print("=" * 50)

for service in services:
    print(f"\nUpdating {service}...")
    
    # Get current task definition
    current_td = ecs.describe_task_definition(taskDefinition=service)['taskDefinition']
    
    # Create new task definition with :latest image
    new_td = {
        'family': current_td['family'],
        'taskRoleArn': current_td.get('taskRoleArn'),
        'executionRoleArn': current_td.get('executionRoleArn'),
        'networkMode': current_td.get('networkMode'),
        'containerDefinitions': current_td['containerDefinitions'],
        'requiresCompatibilities': current_td.get('requiresCompatibilities', []),
        'cpu': current_td.get('cpu'),
        'memory': current_td.get('memory')
    }
    
    # Update image to :latest
    for container in new_td['containerDefinitions']:
        if service in container['image']:
            container['image'] = f"{ECR_BASE}/{service}:latest"
            print(f"  - Updated image to: {container['image']}")
    
    # Remove None values
    new_td = {k: v for k, v in new_td.items() if v is not None}
    
    # Register new task definition
    response = ecs.register_task_definition(**new_td)
    new_revision = response['taskDefinition']['revision']
    print(f"  - New task definition revision: {new_revision}")
    
    # Update service
    ecs.update_service(
        cluster=CLUSTER,
        service=service,
        taskDefinition=f"{service}:{new_revision}",
        forceNewDeployment=True
    )
    print(f"  ✅ {service} updated!")

print("\n🎉 All services updated to use :latest images!")
print("\nWait 2-3 minutes for services to restart, then test CORS.")