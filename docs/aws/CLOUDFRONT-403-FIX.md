# CloudFront 403 Error Fix

## Issue
The frontend at `https://fastship-api.com/` returns a 403 error from CloudFront:
```
ERROR
The request could not be satisfied.
Bad request. We can't connect to the server for this app or website at this time.
```

## Root Cause
When Terraform workflow was triggered, it created a new CloudFront distribution without the custom domain configuration (aliases and certificate). This overwrote the manually configured settings, causing:
1. Loss of custom domain aliases (`app.fastship-api.com`, `fastship-api.com`, `www.fastship-api.com`)
2. Loss of custom SSL certificate configuration
3. Creation of a duplicate distribution (ER88UDVCJERIM - staging/unlinked)

## Solution Steps

### Step 1: Reconfigure CloudFront Distribution Manually

1. Go to AWS Console → CloudFront → Distribution `E3H0EDHBMNOSGI`
2. Click **Edit** on the distribution
3. Configure the following:

   **General Settings:**
   - **Alternate domain names (CNAMEs)**: Add:
     - `app.fastship-api.com`
     - `fastship-api.com`
     - `www.fastship-api.com`
   - **Custom SSL certificate**: Select `fastship-api.com (3e5f495d-2d1e-4dcf-ac48-99bb68cb805f)`
   - **Security policy**: `TLSv1.2_2021 (recommended)`
   - **Default root object**: `index.html`
   - **Comment**: `fastship-dev frontend`

4. Save changes (deployment takes 15-30 minutes)

### Step 2: Update Terraform Configuration

Update `infrastructure/terraform/environments/dev/terraform.tfvars`:

```hcl
# ACM Certificate ARN for CloudFront custom domain (us-east-1 region)
cloudfront_certificate_arn = "arn:aws:acm:us-east-1:337573345298:certificate/3e5f495d-2d1e-4dcf-ac48-99bb68cb805f"

# CloudFront aliases (custom domains)
cloudfront_aliases = ["app.fastship-api.com", "fastship-api.com", "www.fastship-api.com"]
```

### Step 3: Import Distribution into Terraform State

Import the existing distribution so Terraform manages it:

```bash
cd infrastructure/terraform/environments/dev

# Import the distribution
terraform import module.frontend.aws_cloudfront_distribution.frontend E3H0EDHBMNOSGI
```

Or use the helper script:
```bash
./infrastructure/scripts/import-cloudfront-distribution.sh E3H0EDHBMNOSGI
```

### Step 4: Verify and Apply Terraform

```bash
cd infrastructure/terraform/environments/dev

# Check what Terraform wants to change
terraform plan

# If the plan looks correct (should show no changes or only minor updates), apply
terraform apply
```

### Step 5: Delete Duplicate Distribution

After confirming the correct distribution is working:

1. Go to AWS Console → CloudFront
2. Find distribution `ER88UDVCJERIM` (the duplicate)
3. **Disable** the distribution first (required before deletion)
4. Wait for it to be disabled
5. **Delete** the distribution

**Note:** You can also delete it via AWS CLI:
```bash
# Disable first
aws cloudfront update-distribution \
  --id ER88UDVCJERIM \
  --if-match $(aws cloudfront get-distribution-config --id ER88UDVCJERIM --query 'ETag' --output text) \
  --distribution-config file://<(aws cloudfront get-distribution-config --id ER88UDVCJERIM --query 'DistributionConfig' --output json | jq '.Enabled = false') \
  --profile fastship

# Wait for deployment, then delete
aws cloudfront delete-distribution \
  --id ER88UDVCJERIM \
  --if-match $(aws cloudfront get-distribution-config --id ER88UDVCJERIM --query 'ETag' --output text) \
  --profile fastship
```

### Step 6: Verify Certificate Validation

Ensure the DNS validation records are in Route53:

```bash
# Check if validation records exist
aws route53 list-resource-record-sets \
  --hosted-zone-id YOUR_HOSTED_ZONE_ID \
  --profile fastship \
  --query "ResourceRecordSets[?Type=='CNAME' && contains(Name, 'fastship-api.com')]" \
  --output table
```

The certificate should show `ISSUED` status once validation is complete.

## Why This Happened

1. **Terraform workflow triggered**: When the Terraform workflow ran in GitHub Actions, it created a new CloudFront distribution with default settings (no custom domain)
2. **Manual configuration lost**: The manually configured aliases and certificate were not in Terraform state, so Terraform created a new distribution
3. **Duplicate created**: Terraform created `ER88UDVCJERIM` while the original `E3H0EDHBMNOSGI` still existed

## Prevention

After importing and configuring:
- **Always update Terraform first** before making manual changes
- **Use Terraform for all infrastructure changes** to avoid drift
- **Review Terraform plan** before applying in CI/CD

## Current Status

- ✅ Correct distribution: `E3H0EDHBMNOSGI` (ddx58afhk5dnp.cloudfront.net)
- ❌ Duplicate distribution: `ER88UDVCJERIM` (needs deletion)
- ✅ Certificate: `arn:aws:acm:us-east-1:337573345298:certificate/3e5f495d-2d1e-4dcf-ac48-99bb68cb805f`
- ⏳ Certificate status: `PENDING_VALIDATION` (needs DNS validation records)
