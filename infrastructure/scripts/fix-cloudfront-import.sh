#!/bin/bash
set -euo pipefail

# This script fixes CloudFront import by removing the wrong distribution from state
# and importing the correct one.

# Usage: ./fix-cloudfront-import.sh <CORRECT_DISTRIBUTION_ID> [WRONG_DISTRIBUTION_ID]

CORRECT_ID=${1:-E3H0EDHBMNOSGI}
WRONG_ID=${2:-}
ENVIRONMENT="dev"

if [ -z "$CORRECT_ID" ]; then
  echo "Usage: $0 <CORRECT_DISTRIBUTION_ID> [WRONG_DISTRIBUTION_ID]"
  echo "Example: $0 E3H0EDHBMNOSGI ER88UDVCJERIM"
  exit 1
fi

echo "=== Fixing CloudFront Import ==="
echo ""
echo "Correct Distribution ID: $CORRECT_ID"
echo "Environment: $ENVIRONMENT"
echo ""

# Navigate to the Terraform environment directory
cd "$(dirname "$0")/../terraform/environments/${ENVIRONMENT}"

# Check current state
echo "Checking current Terraform state..."
CURRENT_ID=$(terraform state show module.frontend.aws_cloudfront_distribution.frontend 2>/dev/null | grep -E "^id\s*=" | head -1 | awk '{print $3}' | tr -d '"' || echo "")

if [ -n "$CURRENT_ID" ]; then
  echo "Current distribution in state: $CURRENT_ID"
  
  if [ "$CURRENT_ID" = "$CORRECT_ID" ]; then
    echo "✅ Correct distribution already in state!"
    echo "Running terraform plan to verify..."
    terraform plan
    exit 0
  else
    echo "⚠️  Wrong distribution in state. Removing it..."
    
    # Remove from state
    terraform state rm module.frontend.aws_cloudfront_distribution.frontend
    
    echo "✅ Removed wrong distribution from state"
  fi
else
  echo "No distribution currently in state"
fi

# Import the correct distribution
echo ""
echo "Importing correct distribution: $CORRECT_ID"
terraform import module.frontend.aws_cloudfront_distribution.frontend "$CORRECT_ID"

echo ""
echo "✅ Import successful!"
echo ""
echo "Verifying with terraform plan..."
terraform plan

echo ""
echo "=== Next Steps ==="
echo "1. Review the terraform plan above"
echo "2. If the plan looks correct, run: terraform apply"
echo "3. After confirming everything works, delete the duplicate distribution: $WRONG_ID"
echo ""
