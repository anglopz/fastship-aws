variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cloudfront_certificate_arn" {
  description = "ACM certificate ARN for CloudFront custom domain (must be in us-east-1). Leave empty to use default certificate."
  type        = string
  default     = ""
}

variable "cloudfront_aliases" {
  description = "List of aliases (custom domains) for CloudFront distribution"
  type        = list(string)
  default     = []
}
