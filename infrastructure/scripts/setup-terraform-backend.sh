#!/bin/bash

set -e

# Script to set up Terraform S3 backend and DynamoDB state locking
# Usage: ./setup-terraform-backend.sh [dev|prod]

ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-eu-west-1}

# Get AWS account ID
echo "Getting AWS Account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS CLI not configured or credentials not available"
    echo "Please configure AWS CLI first:"
    echo "  aws configure"
    exit 1
fi

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"

# Determine bucket name based on environment
if [ "$ENVIRONMENT" = "dev" ]; then
    BUCKET_NAME="fastship-tf-state-dev"
else
    BUCKET_NAME="fastship-tf-state-prod"
fi

DYNAMODB_TABLE="fastship-tf-locks"

echo ""
echo "Setting up Terraform backend for environment: $ENVIRONMENT"
echo "S3 Bucket: $BUCKET_NAME"
echo "DynamoDB Table: $DYNAMODB_TABLE"
echo ""

# Step 1: Create S3 bucket
echo "Step 1: Creating S3 bucket..."
if aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
    echo "  ✓ Bucket $BUCKET_NAME already exists"
else
    echo "  Creating bucket $BUCKET_NAME..."
    if [ "$AWS_REGION" = "us-east-1" ]; then
        # us-east-1 doesn't need LocationConstraint
        aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION"
    else
        aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION"
    fi
    echo "  ✓ Bucket created"
fi

# Step 2: Enable versioning
echo "Step 2: Enabling bucket versioning..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled \
    --region "$AWS_REGION" > /dev/null
echo "  ✓ Versioning enabled"

# Step 3: Enable encryption
echo "Step 3: Enabling bucket encryption..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }' \
    --region "$AWS_REGION" > /dev/null
echo "  ✓ Encryption enabled"

# Step 4: Block public access
echo "Step 4: Blocking public access..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region "$AWS_REGION" > /dev/null
echo "  ✓ Public access blocked"

# Step 5: Create DynamoDB table for state locking
echo "Step 5: Creating DynamoDB table for state locking..."
if aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --region "$AWS_REGION" > /dev/null 2>&1; then
    echo "  ✓ Table $DYNAMODB_TABLE already exists"
else
    echo "  Creating DynamoDB table $DYNAMODB_TABLE..."
    aws dynamodb create-table \
        --table-name "$DYNAMODB_TABLE" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --region "$AWS_REGION" > /dev/null
    
    echo "  Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name "$DYNAMODB_TABLE" --region "$AWS_REGION"
    echo "  ✓ Table created and active"
fi

echo ""
echo "✅ Terraform backend setup complete!"
echo ""
echo "Summary:"
echo "  S3 Bucket:      $BUCKET_NAME"
echo "  DynamoDB Table: $DYNAMODB_TABLE"
echo "  Region:         $AWS_REGION"
echo ""
echo "Next steps:"
echo "  1. Initialize Terraform in your environment:"
echo "     cd infrastructure/terraform/environments/$ENVIRONMENT"
echo "     terraform init"
echo ""
echo "  2. Verify backend configuration in main.tf uses:"
echo "     bucket = \"$BUCKET_NAME\""
echo "     dynamodb_table = \"$DYNAMODB_TABLE\""
