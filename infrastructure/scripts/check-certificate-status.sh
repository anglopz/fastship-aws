#!/bin/bash

# Check ACM certificate validation status
# Usage: ./check-certificate-status.sh

set -e

export AWS_PROFILE=${AWS_PROFILE:-fastship}

echo "=== ACM Certificate Validation Status ==="
echo ""

# ALB Certificate (eu-west-1)
ALB_CERT_ARN="arn:aws:acm:eu-west-1:337573345298:certificate/872b2b04-d0c4-432c-bbbd-e291df9afdd3"
echo "🔐 ALB Certificate (api.fastship-api.com):"
aws acm describe-certificate \
  --certificate-arn "$ALB_CERT_ARN" \
  --region eu-west-1 \
  --query 'Certificate.{Status:Status,DomainName:DomainName,ValidationStatus:DomainValidationOptions[0].ValidationStatus,ValidationRecord:DomainValidationOptions[0].ResourceRecord}' \
  --output json

echo ""

# CloudFront Certificate (us-east-1)
CLOUDFRONT_CERT_ARN="arn:aws:acm:us-east-1:337573345298:certificate/3e5f495d-2d1e-4dcf-ac48-99bb68cb805f"
echo "🔐 CloudFront Certificate (fastship-api.com, www, app):"
aws acm describe-certificate \
  --certificate-arn "$CLOUDFRONT_CERT_ARN" \
  --region us-east-1 \
  --query 'Certificate.{Status:Status,DomainName:DomainName,SubjectAlternativeNames:SubjectAlternativeNames,ValidationStatus:DomainValidationOptions[0].ValidationStatus}' \
  --output json

echo ""
echo "=== Route53 Validation Records ==="
aws route53 list-resource-record-sets \
  --hosted-zone-id Z07434332R7DSFKAWB26B \
  --query "ResourceRecordSets[?Type=='CNAME' && contains(Name, '_')]" \
  --output table

echo ""
echo "💡 Tip: Run this script every few minutes to check validation progress."
echo "   Certificates should validate within 5-30 minutes after DNS records are correct."
