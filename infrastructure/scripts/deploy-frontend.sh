#!/bin/bash

set -e

# Deploy frontend to S3 and invalidate CloudFront
# Usage: ./deploy-frontend.sh [environment]

ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}

echo "Deploying frontend to ${ENVIRONMENT} environment..."

# Determine S3 bucket and CloudFront distribution based on environment
if [ "$ENVIRONMENT" = "prod" ]; then
    S3_BUCKET="fastship-prod-frontend"
    CLOUDFRONT_DIST_ID=${CLOUDFRONT_DISTRIBUTION_PROD:-""}
else
    S3_BUCKET="fastship-dev-frontend"
    CLOUDFRONT_DIST_ID=${CLOUDFRONT_DISTRIBUTION_DEV:-""}
fi

# Build frontend
echo "Building frontend..."
cd "$(dirname "$0")/../../src/frontend"

# Set API URL based on environment
if [ "$ENVIRONMENT" = "prod" ]; then
    export VITE_API_URL=${VITE_API_URL_PROD:-"https://api.fastship.com"}
else
    export VITE_API_URL=${VITE_API_URL_DEV:-"http://localhost:8000"}
fi

npm ci
npm run build

# Deploy to S3
echo "Deploying to S3 bucket: ${S3_BUCKET}..."
aws s3 sync dist/ s3://${S3_BUCKET}/ \
    --region ${AWS_REGION} \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "*.html"

# Upload HTML files with no cache
aws s3 sync dist/ s3://${S3_BUCKET}/ \
    --region ${AWS_REGION} \
    --delete \
    --cache-control "no-cache, no-store, must-revalidate" \
    --include "*.html"

# Invalidate CloudFront if distribution ID is provided
if [ -n "$CLOUDFRONT_DIST_ID" ]; then
    echo "Invalidating CloudFront distribution: ${CLOUDFRONT_DIST_ID}..."
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id ${CLOUDFRONT_DIST_ID} \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    
    echo "CloudFront invalidation created: ${INVALIDATION_ID}"
    echo "Waiting for invalidation to complete..."
    aws cloudfront wait invalidation-completed \
        --distribution-id ${CLOUDFRONT_DIST_ID} \
        --id ${INVALIDATION_ID}
    
    echo "CloudFront invalidation completed!"
else
    echo "Warning: CloudFront distribution ID not set. Skipping invalidation."
fi

echo "Frontend deployment completed successfully!"
