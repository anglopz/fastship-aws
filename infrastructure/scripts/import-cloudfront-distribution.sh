#!/bin/bash
set -euo pipefail

# This script imports an existing CloudFront distribution into Terraform state.
# It's used when a distribution is created manually (e.g., via AWS Console)
# and needs to be brought under Terraform management.

# Usage: ./import-cloudfront-distribution.sh <DISTRIBUTION_ID>

DISTRIBUTION_ID=$1
ENVIRONMENT="dev" # Assuming 'dev' environment for now

if [ -z "$DISTRIBUTION_ID" ]; then
  echo "Usage: $0 <DISTRIBUTION_ID>"
  echo "Example: $0 E3H0EDHBMNOSGI"
  exit 1
fi

echo "=== Importing Existing CloudFront Distribution ==="
echo ""
echo "Distribution ID: $DISTRIBUTION_ID"
echo "Environment: $ENVIRONMENT"
echo ""

# Navigate to the Terraform environment directory
cd "$(dirname "$0")/../terraform/environments/${ENVIRONMENT}"

# Run terraform import
# The resource address for the CloudFront distribution is module.frontend.aws_cloudfront_distribution.frontend
terraform import "module.frontend.aws_cloudfront_distribution.frontend" "$DISTRIBUTION_ID"

echo ""
echo "✅ Import successful!"
echo ""
echo "Next steps:"
echo "1. Run 'terraform plan' to see what Terraform wants to change"
echo "2. If there are differences, update terraform.tfvars with:"
echo "   - cloudfront_certificate_arn"
echo "   - cloudfront_aliases"
echo "3. Run 'terraform apply' to sync the configuration"
echo ""
