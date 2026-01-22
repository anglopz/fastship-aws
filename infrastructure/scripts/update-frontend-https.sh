#!/bin/bash
set -e

# Update and deploy frontend with HTTPS API URL
# Usage: ./update-frontend-https.sh [environment] [api_url]

ENVIRONMENT=${1:-dev}
API_URL=${2:-"https://api.fastship-api.com"}
AWS_REGION=${AWS_REGION:-eu-west-1}
AWS_PROFILE=${AWS_PROFILE:-fastship}

echo "🚀 Updating frontend with HTTPS API URL..."
echo "API URL: ${API_URL}"
echo ""

# Get Terraform outputs
cd "$(dirname "$0")/../terraform/environments/${ENVIRONMENT}"
export AWS_PROFILE=${AWS_PROFILE}

S3_BUCKET=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "fastship-${ENVIRONMENT}-frontend")
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")

# Navigate to frontend directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/src/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Error: Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# Set API URL for build
export VITE_API_URL="${API_URL}"

echo "📦 Building frontend with API URL: ${VITE_API_URL}"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies..."
    npm install
fi

# Build
echo "🔨 Building production bundle..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Build failed: dist/ directory not found"
    exit 1
fi

# Deploy to S3
echo "☁️  Deploying to S3 bucket: ${S3_BUCKET}..."
aws s3 sync ./dist/ \
    s3://${S3_BUCKET}/ \
    --delete \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "*.html" \
    --exclude "*.json"

# Upload HTML files with shorter cache
aws s3 sync ./dist/ \
    s3://${S3_BUCKET}/ \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} \
    --cache-control "public, max-age=0, must-revalidate" \
    --include "*.html" \
    --include "*.json"

echo "✅ Frontend deployed to S3"

# Invalidate CloudFront cache
if [ -n "$CLOUDFRONT_ID" ]; then
    echo "🔄 Invalidating CloudFront cache..."
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id ${CLOUDFRONT_ID} \
        --paths "/*" \
        --region ${AWS_REGION} \
        --profile ${AWS_PROFILE} \
        --query 'Invalidation.Id' \
        --output text)
    
    echo "✅ CloudFront cache invalidation created: ${INVALIDATION_ID}"
    echo "   This may take 1-5 minutes to complete"
else
    echo "⚠️  Skipping CloudFront cache invalidation (distribution ID not found)"
fi

echo ""
echo "✅ Frontend update complete!"
echo "   Frontend now uses HTTPS API URL: ${API_URL}"
