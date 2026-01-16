# Terraform Backend Setup Guide

This guide explains how to set up the S3 backend and DynamoDB state locking for Terraform.

> **Note**: For general AWS deployment documentation, see `../../docs/aws/`.

## Quick Setup

Run the setup script:

```bash
# For dev environment
./infrastructure/scripts/setup-terraform-backend.sh dev

# For prod environment
./infrastructure/scripts/setup-terraform-backend.sh prod
```

## Manual Setup

If you prefer to set up manually, follow these steps:

### 1. Get AWS Account ID

```bash
aws sts get-caller-identity --query Account --output text
```

### 2. Create S3 Bucket for Dev

```bash
AWS_REGION="eu-west-1"
BUCKET_NAME="fastship-tf-state-dev"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled \
  --region $AWS_REGION

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }' \
  --region $AWS_REGION

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
  --region $AWS_REGION
```

### 3. Create DynamoDB Table for State Locking

```bash
DYNAMODB_TABLE="fastship-tf-locks"
AWS_REGION="eu-west-1"

aws dynamodb create-table \
  --table-name $DYNAMODB_TABLE \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region $AWS_REGION

# Wait for table to be active
aws dynamodb wait table-exists --table-name $DYNAMODB_TABLE --region $AWS_REGION
```

### 4. Initialize Terraform

```bash
cd infrastructure/terraform/environments/dev
terraform init
```

## Backend Configuration

Each environment has its own backend configuration in `environments/{env}/main.tf`:

**Dev Environment** (`environments/dev/main.tf`):
```hcl
backend "s3" {
  bucket         = "fastship-tf-state-dev"
  key            = "terraform.tfstate"
  region         = "eu-west-1"
  encrypt        = true
  dynamodb_table = "fastship-tf-locks"
}
```

**Prod Environment** (`environments/prod/main.tf`):
- Uses `fastship-tf-state-prod` bucket
- Same DynamoDB table: `fastship-tf-locks`

## Important Notes

1. **The root `backend.tf` is not used** - Each environment has its own backend config in `main.tf`
2. **S3 bucket names**:
   - Dev: `fastship-tf-state-dev`
   - Prod: `fastship-tf-state-prod`
3. **DynamoDB table** is shared: `fastship-tf-locks` (one table for all environments)
4. **Region**: All backend resources are in `eu-west-1`

## Verification

After setup, verify the resources exist:

```bash
# Check S3 bucket
aws s3 ls | grep fastship-tf-state

# Check DynamoDB table
aws dynamodb list-tables --region eu-west-1 | grep fastship-tf-locks

# Check bucket versioning
aws s3api get-bucket-versioning --bucket fastship-tf-state-dev --region eu-west-1

# Check bucket encryption
aws s3api get-bucket-encryption --bucket fastship-tf-state-dev --region eu-west-1
```

## Troubleshooting

### Error: "Backend initialization required"
Run `terraform init` in the environment directory:
```bash
cd infrastructure/terraform/environments/dev
terraform init
```

### Error: "Bucket does not exist"
Create the bucket using the setup script or manual commands above.

### Error: "Access Denied"
Check your AWS credentials and IAM permissions:
- `s3:CreateBucket`
- `s3:PutBucketVersioning`
- `s3:PutBucketEncryption`
- `s3:PutObject`
- `s3:GetObject`
- `dynamodb:CreateTable`
- `dynamodb:PutItem`
- `dynamodb:GetItem`

### Error: "Table already exists"
The DynamoDB table might already exist. Check with:
```bash
aws dynamodb describe-table --table-name fastship-tf-locks --region eu-west-1
```

If it exists but is in a different region, either:
1. Delete it and recreate in the correct region, or
2. Update the backend config to use the existing table's region
