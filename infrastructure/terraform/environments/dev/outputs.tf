output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = try(module.networking[0].alb_dns_name, null)
}

output "alb_arn" {
  description = "Application Load Balancer ARN"
  value       = try(module.networking[0].alb_arn, null)
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.frontend.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = module.frontend.cloudfront_distribution_id
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.frontend.s3_bucket_name
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = try(module.rds[0].db_endpoint, null)
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = try(module.redis[0].redis_endpoint, null)
}

output "ecs_cluster_id" {
  description = "ECS cluster ID"
  value       = try(module.ecs[0].cluster_id, null)
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = try(module.ecs[0].cluster_name, null)
}

output "api_service_name" {
  description = "ECS API service name"
  value       = try(module.ecs[0].api_service_name, null)
}

output "celery_worker_service_name" {
  description = "ECS Celery worker service name"
  value       = try(module.ecs[0].celery_worker_service_name, null)
}

output "api_url" {
  description = "API URL"
  value       = try("http://${module.networking[0].alb_dns_name}", null)
}

output "ecr_repository_url" {
  description = "ECR repository URL for backend Docker image"
  value       = module.ecr.repository_url
}

output "ecr_repository_uri" {
  description = "ECR repository URI (for Docker push/pull)"
  value       = module.ecr.repository_uri
}
