#!/usr/bin/env bash
set -euo pipefail

# Spin up FastShip AWS services for demos or development
# Creates: ECS services, RDS database, Redis cache, ALB
# Typical spin-up time: ~8-12 minutes (RDS creation is the bottleneck)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/../terraform/environments/dev"
TFVARS="$TF_DIR/terraform.tfvars"

echo "=== FastShip Spin Up ==="
echo "This will create: ECS services (API + Celery), RDS PostgreSQL, Redis, ALB"
echo "Estimated time: ~8-12 minutes"
echo "Estimated cost while running: ~\$3-5/day"
echo ""

read -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Toggle services_enabled to true
sed -i 's/^services_enabled = false/services_enabled = true/' "$TFVARS"
echo "Set services_enabled = true in terraform.tfvars"

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

echo ""
echo "Applying... (this takes ~8-12 minutes)"
terraform apply -var-file=terraform.tfvars -auto-approve

echo ""
echo "=== Spin Up Complete ==="
echo ""
echo "Live URLs:"
echo "  API:      https://api.fastship-api.com"
echo "  Health:   https://api.fastship-api.com/health"
echo "  Docs:     https://api.fastship-api.com/docs"
echo "  Frontend: https://app.fastship-api.com"
echo ""
echo "Note: ECS tasks may take 2-3 minutes after Terraform completes to pass health checks."
echo "Check status: aws ecs describe-services --cluster dev-fastship-cluster --services dev-api --query 'services[0].runningCount' --profile fastship --region eu-west-1"
echo ""
echo "Remember to spin down when done: ./spin-down.sh"
