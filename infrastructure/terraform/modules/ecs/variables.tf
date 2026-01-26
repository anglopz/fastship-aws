variable "project_name" {
  description = "Project name"
  type        = string
  default     = "fastship"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "backend_image" {
  description = "Backend Docker image URI"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs (required if api_use_public_subnets is true)"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "ECS security group ID"
  type        = string
}

variable "target_group_arn" {
  description = "Target group ARN for ALB"
  type        = string
  default     = ""
}

variable "api_task_cpu" {
  description = "CPU units for API task (1024 = 1 vCPU)"
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
  description = "Whether to use public subnets for API service (default: false for security)"
  type        = bool
  default     = false
}

variable "worker_task_cpu" {
  description = "CPU units for Celery worker task (1024 = 1 vCPU)"
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
  description = "Whether to run Celery worker in public subnets (needed for outbound internet access when NAT Gateway is disabled, e.g. Mailtrap SMTP)"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "container_environment" {
  description = "Container environment variables"
  type        = list(map(string))
  default     = []
}

variable "container_secrets" {
  description = "Container secrets from AWS Secrets Manager"
  type        = list(map(string))
  default     = []
}
