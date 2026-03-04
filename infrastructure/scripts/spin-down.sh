#!/usr/bin/env bash
set -euo pipefail

# Spin down FastShip AWS services to minimize costs
# Keeps: VPC, S3+CloudFront (frontend), ECR, Route53
# Destroys: ECS, RDS, Redis, ALB

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/../terraform/environments/dev"
TFVARS="$TF_DIR/terraform.tfvars"

echo "=== FastShip Spin Down ==="
echo "This will destroy: ECS services, RDS database, Redis cache, ALB"
echo "This will keep: Frontend (S3+CloudFront), VPC, ECR, Route53"
echo ""

# Check current state
CURRENT=$(grep -E '^services_enabled' "$TFVARS" | awk '{print $3}')
if [ "$CURRENT" = "false" ]; then
  echo "Services are already disabled in terraform.tfvars"
  echo "Run 'terraform apply' if the resources still exist in AWS."
fi

read -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Toggle services_enabled to false
sed -i 's/^services_enabled = true/services_enabled = false/' "$TFVARS"
echo "Set services_enabled = false in terraform.tfvars"

# Run terraform
cd "$TF_DIR"
export AWS_PROFILE="${AWS_PROFILE:-fastship}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"

echo ""
echo "Running terraform plan..."
terraform plan -var-file=terraform.tfvars

echo ""
read -p "Apply this plan? (y/N): " apply_confirm
if [[ ! "$apply_confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted. terraform.tfvars was already updated — revert manually if needed."
  exit 0
fi

terraform apply -var-file=terraform.tfvars -auto-approve

echo ""
echo "=== Spin Down Complete ==="
echo "Destroyed: ECS, RDS, Redis, ALB"
echo "Still running: Frontend at https://app.fastship-api.com"
echo "Estimated monthly cost: ~\$1-3"
echo ""
echo "To spin back up: ./spin-up.sh"
