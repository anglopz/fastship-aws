#!/bin/bash

set -e

# Build and push Docker image to ECR
# Usage: ./build-and-push.sh [environment] [image-tag]

ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REPOSITORY="fastship-backend"
IMAGE_TAG=${2:-latest}

echo "Building Docker image for ${ENVIRONMENT} environment..."
echo "AWS Account: ${AWS_ACCOUNT_ID}"
echo "AWS Region: ${AWS_REGION}"
echo "Repository: ${ECR_REPOSITORY}"
echo "Image Tag: ${IMAGE_TAG}"

# Get ECR login token
echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Check if repository exists, create if not
if ! aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} &>/dev/null; then
    echo "Creating ECR repository ${ECR_REPOSITORY}..."
    aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}
fi

# Build image
echo "Building Docker image..."
cd "$(dirname "$0")/../../src/backend"
docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} .

# Tag image
ECR_IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_IMAGE_URI}
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

# Push image
echo "Pushing image to ECR..."
docker push ${ECR_IMAGE_URI}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

echo "Successfully pushed ${ECR_IMAGE_URI}"
echo "Image URI: ${ECR_IMAGE_URI}"
