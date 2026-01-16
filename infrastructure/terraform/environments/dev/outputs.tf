output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.networking.alb_dns_name
}

output "alb_arn" {
  description = "Application Load Balancer ARN"
  value       = module.networking.alb_arn
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.frontend.cloudfront_domain_name
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.redis_endpoint
}

output "ecs_cluster_id" {
  description = "ECS cluster ID"
  value       = module.ecs.cluster_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "api_service_name" {
  description = "ECS API service name"
  value       = module.ecs.api_service_name
}

output "celery_worker_service_name" {
  description = "ECS Celery worker service name"
  value       = module.ecs.celery_worker_service_name
}

output "api_url" {
  description = "API URL"
  value       = "http://${module.networking.alb_dns_name}"
}
