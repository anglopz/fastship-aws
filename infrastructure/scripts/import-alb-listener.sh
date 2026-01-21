#!/bin/bash

# Import existing ALB HTTPS listener into Terraform state
# Usage: ./import-alb-listener.sh [environment]

set -e

ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-eu-west-1}
AWS_PROFILE=${AWS_PROFILE:-fastship}

echo "=== Importing ALB HTTPS Listener into Terraform ==="
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Navigate to terraform directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../terraform/environments/$ENVIRONMENT"

if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "❌ Error: Terraform directory not found at $TERRAFORM_DIR"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Get ALB ARN from Terraform output
echo "📋 Getting ALB ARN from Terraform..."
ALB_ARN=$(terraform output -raw alb_arn 2>/dev/null || echo "")

if [ -z "$ALB_ARN" ]; then
    echo "⚠️  ALB ARN not found in Terraform outputs. Trying to get from AWS..."
    ALB_NAME="fastship-${ENVIRONMENT}-alb"
    ALB_ARN=$(aws elbv2 describe-load-balancers \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query "LoadBalancers[?LoadBalancerName=='${ALB_NAME}'].LoadBalancerArn" \
        --output text)
fi

if [ -z "$ALB_ARN" ]; then
    echo "❌ Error: Could not find ALB ARN"
    exit 1
fi

echo "ALB ARN: $ALB_ARN"
echo ""

# Get existing HTTPS listener ARN
echo "📋 Getting existing HTTPS listener..."
HTTPS_LISTENER_ARN=$(aws elbv2 describe-listeners \
    --load-balancer-arn "$ALB_ARN" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query 'Listeners[?Protocol==`HTTPS`].ListenerArn' \
    --output text)

if [ -z "$HTTPS_LISTENER_ARN" ]; then
    echo "❌ Error: No HTTPS listener found on ALB"
    exit 1
fi

echo "HTTPS Listener ARN: $HTTPS_LISTENER_ARN"
echo ""

# Check if already imported
echo "📋 Checking if listener is already in Terraform state..."
if terraform state list | grep -q "module.networking.aws_lb_listener.backend_https"; then
    echo "✅ Listener already in Terraform state"
    echo "   Checking if it matches..."
    STATE_ARN=$(terraform state show "module.networking.aws_lb_listener.backend_https[0]" 2>/dev/null | grep "arn" | head -1 | awk '{print $3}' || echo "")
    if [ "$STATE_ARN" = "$HTTPS_LISTENER_ARN" ]; then
        echo "✅ State matches existing listener. No import needed."
        exit 0
    else
        echo "⚠️  State has different listener ARN. May need to remove and reimport."
    fi
fi

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo "📋 Initializing Terraform..."
    terraform init
fi

# Import the listener
echo "📋 Importing listener into Terraform state..."
echo "Command: terraform import 'module.networking.aws_lb_listener.backend_https[0]' '$HTTPS_LISTENER_ARN'"
echo ""

terraform import \
    -var-file=terraform.tfvars \
    "module.networking.aws_lb_listener.backend_https[0]" \
    "$HTTPS_LISTENER_ARN"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully imported HTTPS listener!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Run: terraform plan -var-file=terraform.tfvars"
    echo "   2. Verify no unexpected changes"
    echo "   3. Run: terraform apply -var-file=terraform.tfvars (if needed)"
else
    echo ""
    echo "❌ Import failed. Check the error message above."
    exit 1
fi
