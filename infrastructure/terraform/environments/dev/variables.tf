variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets. Set to false for free-tier (saves ~$32/month). Note: RDS/Redis in private subnets won't have internet access without NAT."
  type        = bool
  default     = false
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "fastship"
}

variable "username" {
  description = "Database master username"
  type        = string
  default     = "fastship"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "backup_retention_period" {
  description = "RDS backup retention period in days (max 1 for free tier)"
  type        = number
  default     = 1
}

variable "engine_version" {
  description = "PostgreSQL engine version (available in eu-west-1: 15.10, 15.15, 16.6, 16.11, 17.7, 18.1)"
  type        = string
  default     = "15.15"  # Latest 15.x version - best security/features for 15.x series
}

variable "node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

variable "redis_auth_token" {
  description = "Redis authentication token"
  type        = string
  sensitive   = true
}

variable "backend_image" {
  description = "Backend Docker image URI"
  type        = string
  default     = ""
}

variable "api_task_cpu" {
  description = "CPU units for API task"
  type        = number
  default     = 512
}

variable "api_task_memory" {
  description = "Memory for API task in MB"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 1
}

variable "api_use_public_subnets" {
  description = "Whether to use public subnets for API service"
  type        = bool
  default     = false
}

variable "worker_task_cpu" {
  description = "CPU units for Celery worker task"
  type        = number
  default     = 256
}

variable "worker_task_memory" {
  description = "Memory for Celery worker task in MB"
  type        = number
  default     = 512
}

variable "worker_desired_count" {
  description = "Desired number of Celery worker tasks"
  type        = number
  default     = 1
}

variable "worker_use_public_subnets" {
  description = "Whether to run Celery worker in public subnets (needed for Mailtrap SMTP when NAT Gateway is disabled)"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "domain_name" {
  description = "Domain name for frontend (optional)"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS listener (must be in eu-west-1 for ALB). Leave empty if not using HTTPS yet."
  type        = string
  default     = ""
}

variable "cloudfront_certificate_arn" {
  description = "ACM certificate ARN for CloudFront custom domain (must be in us-east-1). Leave empty to use default certificate."
  type        = string
  default     = ""
}

variable "cloudfront_aliases" {
  description = "List of aliases (custom domains) for CloudFront distribution (e.g., ['app.fastship-api.com', 'fastship-api.com'])"
  type        = list(string)
  default     = []
}

variable "mailtrap_username" {
  description = "Mailtrap username for email sandbox testing"
  type        = string
  sensitive   = true
  default     = ""
}

variable "mailtrap_password" {
  description = "Mailtrap password for email sandbox testing"
  type        = string
  sensitive   = true
  default     = ""
}
