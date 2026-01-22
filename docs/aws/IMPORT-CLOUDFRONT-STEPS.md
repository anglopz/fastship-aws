# Import CloudFront Distribution - Step by Step

## Current Situation
- Terraform state has a CloudFront distribution (probably the wrong one: ER88UDVCJERIM)
- You need to import the correct one: E3H0EDHBMNOSGI
- The error "Resource already managed by Terraform" means we need to remove the existing one first

## Steps to Fix

### Step 1: Set AWS Credentials
```bash
export AWS_PROFILE=fastship
export AWS_REGION=eu-west-1
```

### Step 2: Navigate to Terraform Directory
```bash
cd infrastructure/terraform/environments/dev
```

### Step 3: Check Current State
```bash
terraform state list | grep cloudfront
```

This will show if there's a distribution in state.

### Step 4: Remove Wrong Distribution from State
```bash
terraform state rm module.frontend.aws_cloudfront_distribution.frontend
```

**Note:** This only removes it from Terraform state, it doesn't delete the actual AWS resource.

### Step 5: Import Correct Distribution
```bash
terraform import module.frontend.aws_cloudfront_distribution.frontend E3H0EDHBMNOSGI
```

### Step 6: Verify Configuration
```bash
terraform plan
```

**Expected result:**
- Should show minimal or no changes
- The aliases and certificate should match your manual configuration
- If there are differences, review them carefully

### Step 7: Apply (if needed)
```bash
# Only if plan shows acceptable changes
terraform apply
```

## Alternative: Use the Helper Script

```bash
# Make sure AWS credentials are set
export AWS_PROFILE=fastship

# Run the fix script
./infrastructure/scripts/fix-cloudfront-import.sh E3H0EDHBMNOSGI ER88UDVCJERIM
```

This script will:
1. Check what's in state
2. Remove the wrong distribution if needed
3. Import the correct one
4. Run terraform plan to verify

## Troubleshooting

### If import fails with "Resource already managed"
- The distribution is already in state
- Use `terraform state rm` to remove it first
- Then import again

### If plan shows many changes
- Check that `terraform.tfvars` has the correct values:
  - `cloudfront_certificate_arn`
  - `cloudfront_aliases`
- The plan should match your manual configuration

### If certificate shows as different
- Make sure the ARN in `terraform.tfvars` matches the certificate you configured manually
- Certificate must be in `us-east-1` for CloudFront
