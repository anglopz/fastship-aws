# GitHub Secrets Configuration Guide

This document outlines the required GitHub Secrets for the CI/CD pipelines.

## Required Secrets

Configure these secrets in your GitHub repository settings:
**Settings → Secrets and variables → Actions → New repository secret**

### 1. AWS Credentials

```
AWS_ACCESS_KEY_ID
```
- **Description**: Your AWS Access Key ID
- **How to get**: AWS IAM Console → Users → Your User → Security Credentials → Access Keys
- **Required for**: All workflows (Terraform, Backend, Frontend)

```
AWS_SECRET_ACCESS_KEY
```
- **Description**: Your AWS Secret Access Key
- **How to get**: Generated when creating the Access Key (save it securely - you can only see it once)
- **Required for**: All workflows (Terraform, Backend, Frontend)

### 2. CloudFront Distribution ID

```
CLOUDFRONT_DISTRIBUTION_ID
```
- **Description**: CloudFront distribution ID for frontend deployment
- **How to get**: After running Terraform, get from outputs:
  ```bash
  cd infrastructure/terraform/environments/dev
  terraform output cloudfront_distribution_id
  ```
- **Required for**: Frontend workflow (CloudFront cache invalidation)

## Optional Secrets (for enhanced workflows)

### Frontend Environment Variables

```
VITE_API_URL_DEV
```
- **Description**: API URL for development frontend builds
- **Example**: `http://dev-api.example.com`
- **Required for**: Frontend builds (if using environment-specific API URLs)

```
VITE_API_URL_PROD
```
- **Description**: API URL for production frontend builds
- **Example**: `https://api.example.com`
- **Required for**: Frontend builds (if using environment-specific API URLs)

## Setup Instructions

1. **Create IAM User for CI/CD**:
   ```bash
   # Create user
   aws iam create-user --user-name github-actions
   
   # Attach policies (or create custom policy with minimal permissions)
   aws iam attach-user-policy \
     --user-name github-actions \
     --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
   
   # Create access key
   aws iam create-access-key --user-name github-actions
   ```

2. **Add Secrets to GitHub**:
   - Go to your repository on GitHub
   - Navigate to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Add each secret name and value

3. **Get CloudFront Distribution ID** (after first Terraform deploy):
   ```bash
   cd infrastructure/terraform/environments/dev
   terraform output cloudfront_distribution_id
   ```
   Copy the output and add it as `CLOUDFRONT_DISTRIBUTION_ID` secret.

## Security Best Practices

1. **Use Least Privilege**: Create a custom IAM policy with only the permissions needed for CI/CD
2. **Rotate Keys Regularly**: Update access keys every 90 days
3. **Use Environment Secrets**: For production, use GitHub Environments with additional protection
4. **Never Commit Secrets**: Never commit `.env` files or secrets to the repository
5. **Use AWS IAM Roles**: Consider using OIDC for GitHub Actions instead of access keys (more secure)

## Minimal IAM Policy Example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:*",
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:ListInvalidations"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "terraform-state-*:GetObject",
        "terraform-state-*:PutObject"
      ],
      "Resource": "arn:aws:s3:::fastship-tf-state-*/*"
    }
  ]
}
```

## Troubleshooting

- **"Access Denied" errors**: Check IAM permissions
- **"ECR repository not found"**: Ensure repository exists or create it first
- **"ECS service not found"**: Ensure Terraform has been applied and service exists
- **"CloudFront distribution not found"**: Check the distribution ID in AWS Console
