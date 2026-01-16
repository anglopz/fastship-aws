#!/bin/bash

set -e

# Deploy backend to ECS
# Usage: ./deploy-backend.sh [environment] [image-uri]

ENVIRONMENT=${1:-dev}
IMAGE_URI=${2}
AWS_REGION=${AWS_REGION:-us-east-1}

if [ -z "$IMAGE_URI" ]; then
    echo "Error: Image URI is required"
    echo "Usage: ./deploy-backend.sh [environment] [image-uri]"
    exit 1
fi

echo "Deploying backend to ${ENVIRONMENT} environment..."
echo "Image URI: ${IMAGE_URI}"

CLUSTER_NAME="fastship-${ENVIRONMENT}-cluster"
SERVICE_NAME="fastship-${ENVIRONMENT}-backend"
TASK_DEFINITION_FAMILY="fastship-${ENVIRONMENT}-backend"

# Get current task definition
echo "Getting current task definition..."
CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition ${TASK_DEFINITION_FAMILY} \
    --region ${AWS_REGION} \
    --query 'taskDefinition' \
    --output json)

# Update task definition with new image
echo "Updating task definition with new image..."
NEW_TASK_DEF=$(echo $CURRENT_TASK_DEF | jq --arg IMAGE "$IMAGE_URI" '.containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn) | del(.revision) | del(.status) | del(.requiresAttributes) | del(.placementConstraints) | del(.compatibilities) | del(.registeredAt) | del(.registeredBy)')

# Register new task definition
echo "Registering new task definition..."
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --region ${AWS_REGION} \
    --cli-input-json "$NEW_TASK_DEF" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "New task definition registered: ${NEW_TASK_DEF_ARN}"

# Update service
echo "Updating ECS service..."
aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --task-definition ${NEW_TASK_DEF_ARN} \
    --region ${AWS_REGION} \
    --force-new-deployment \
    > /dev/null

echo "Service update initiated. Waiting for deployment to stabilize..."

# Wait for service to stabilize
aws ecs wait services-stable \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --region ${AWS_REGION}

echo "Deployment completed successfully!"
