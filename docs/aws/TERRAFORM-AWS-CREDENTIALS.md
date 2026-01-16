# Terraform AWS Credentials Setup

## Issue

Terraform needs AWS credentials to access the S3 backend for state storage. If you see:

```
Error: No valid credential sources found
Error: failed to refresh cached credentials, no EC2 IMDS role found
```

This means Terraform isn't finding your AWS credentials.

## Solution: Set AWS_PROFILE Environment Variable

### Option 1: Export for Current Session

```bash
export AWS_PROFILE=fastship
export AWS_REGION=eu-west-1

# Now terraform commands will work
cd infrastructure/terraform/environments/dev
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### Option 2: Use AWS Profile in Each Command

```bash
AWS_PROFILE=fastship terraform output -raw ecr_repository_uri
```

### Option 3: Add to Your Shell Profile

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export AWS_PROFILE=fastship
export AWS_REGION=eu-west-1
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Verify AWS Credentials

```bash
aws sts get-caller-identity --profile fastship
```

Should show:
```json
{
    "UserId": "...",
    "Account": "337573345298",
    "Arn": "arn:aws:iam::337573345298:user/..."
}
```

## Terraform Backend Configuration

The Terraform backend in `infrastructure/terraform/environments/dev/main.tf` uses an S3 backend:

```hcl
terraform {
  backend "s3" {
    bucket         = "fastship-tf-state-337573345298"
    key            = "dev/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "fastship-tf-locks"
  }
}
```

This requires AWS credentials to read/write state files. The `AWS_PROFILE` environment variable tells Terraform which AWS credentials to use.

## Alternative: Use AWS Credentials Directly

If you prefer not to use profiles, set environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="eu-west-1"
```

**Note**: This is less secure than using AWS profiles. Use profiles in `~/.aws/credentials` instead.
