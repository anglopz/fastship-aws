# Fix CloudFront Duplicate Distribution Issue

## Problem Summary
- **Correct distribution**: `E3H0EDHBMNOSGI` (ddx58afhk5dnp.cloudfront.net) - lost custom domain config
- **Duplicate distribution**: `ER88UDVCJERIM` (d1krjjrm03jfnm.cloudfront.net) - created by Terraform workflow
- **Root cause**: Terraform workflow created a new distribution without custom domain settings

## Solution Steps

### Step 1: Manually Reconfigure Correct Distribution ✅

1. Go to **AWS Console → CloudFront → Distribution `E3H0EDHBMNOSGI`**
2. Click **Edit** (General tab)
3. Configure:

   **Alternate domain names (CNAMEs):**
   ```
   app.fastship-api.com
   fastship-api.com
   www.fastship-api.com
   ```

   **Custom SSL certificate:**
   - Select: `fastship-api.com (3e5f495d-2d1e-4dcf-ac48-99bb68cb805f)`
   - Security policy: `TLSv1.2_2021 (recommended)`

   **Other settings:**
   - Default root object: `index.html`
   - Comment: `fastship-dev frontend`

4. **Save changes** (deployment takes 15-30 minutes)

### Step 2: Verify Certificate Validation ⏳

The certificate is `PENDING_VALIDATION`. Ensure DNS validation records are in Route53:

```bash
# Check certificate status
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:337573345298:certificate/3e5f495d-2d1e-4dcf-ac48-99bb68cb805f \
  --region us-east-1 \
  --profile fastship \
  --query 'Certificate.DomainValidationOptions[*].ResourceRecord' \
  --output json
```

Add these CNAME records to Route53 if missing:
- `_6905a0e8d6e96ca5d94cef1f158b8df8.fastship-api.com.` → `_ae578792b454b29f9882cc5959d0825d.jkddzztszm.acm-validations.aws.`
- `_d0c5f9b4b71fdef83d0fec780382bd19.www.fastship-api.com.` → `_7250a75ab942fcdb3e1dd724b8286dcc.jkddzztszm.acm-validations.aws.`
- `_6e1fbdcf57ae16e979eb75812049ea0a.app.fastship-api.com.` → `_44d8481654f9b0fc2510bd5455d3d9fe.jkddzztszm.acm-validations.aws.`

### Step 3: Import Distribution into Terraform State

After manual configuration is complete and deployed:

```bash
cd infrastructure/terraform/environments/dev

# Import the existing distribution
terraform import module.frontend.aws_cloudfront_distribution.frontend E3H0EDHBMNOSGI
```

Or use the helper script:
```bash
./infrastructure/scripts/import-cloudfront-distribution.sh E3H0EDHBMNOSGI
```

### Step 4: Verify Terraform Plan

```bash
cd infrastructure/terraform/environments/dev

# Check what Terraform wants to change
terraform plan
```

**Expected result**: Should show minimal or no changes (Terraform should match your manual configuration).

If there are differences:
- Review the plan carefully
- The aliases and certificate should match what you configured manually
- If not, update `terraform.tfvars` and run `terraform plan` again

### Step 5: Apply Terraform (if needed)

```bash
# Only apply if plan shows acceptable changes
terraform apply
```

### Step 6: Delete Duplicate Distribution

**After confirming the correct distribution works:**

1. **Disable** distribution `ER88UDVCJERIM`:
   ```bash
   aws cloudfront get-distribution-config \
     --id ER88UDVCJERIM \
     --profile fastship \
     --query '{ETag:ETag,Config:DistributionConfig}' \
     --output json > /tmp/dist-config.json
   
   # Edit config to set Enabled = false, then:
   aws cloudfront update-distribution \
     --id ER88UDVCJERIM \
     --distribution-config file:///tmp/dist-config.json \
     --if-match $(cat /tmp/dist-config.json | jq -r '.ETag') \
     --profile fastship
   ```

2. **Wait for deployment** (15-30 minutes)

3. **Delete** the distribution:
   ```bash
   aws cloudfront delete-distribution \
     --id ER88UDVCJERIM \
     --if-match $(aws cloudfront get-distribution-config --id ER88UDVCJERIM --query 'ETag' --output text) \
     --profile fastship
   ```

Or use AWS Console:
1. Go to CloudFront → Distribution `ER88UDVCJERIM`
2. Click **Disable** → Wait for deployment
3. Click **Delete**

## Terraform Configuration Updated ✅

The following files have been updated:

1. ✅ `infrastructure/terraform/modules/frontend/variables.tf` - Added `cloudfront_certificate_arn` and `cloudfront_aliases`
2. ✅ `infrastructure/terraform/modules/frontend/main.tf` - Updated to use custom certificate and aliases
3. ✅ `infrastructure/terraform/environments/dev/variables.tf` - Added variables
4. ✅ `infrastructure/terraform/environments/dev/main.tf` - Pass variables to frontend module
5. ✅ `infrastructure/terraform/environments/dev/terraform.tfvars` - Added certificate ARN and aliases

## Prevention

After this fix:
- ✅ Terraform will manage the distribution with custom domain settings
- ✅ Future Terraform workflows won't overwrite the configuration
- ✅ All infrastructure changes should go through Terraform

## Current Configuration

- **Distribution ID**: `E3H0EDHBMNOSGI`
- **Domain**: `ddx58afhk5dnp.cloudfront.net`
- **Certificate ARN**: `arn:aws:acm:us-east-1:337573345298:certificate/3e5f495d-2d1e-4dcf-ac48-99bb68cb805f`
- **Aliases**: `app.fastship-api.com`, `fastship-api.com`, `www.fastship-api.com`
- **Certificate Status**: `PENDING_VALIDATION` (needs DNS validation)
