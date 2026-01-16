output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "api_service_name" {
  description = "ECS API service name"
  value       = aws_ecs_service.api.name
}

output "celery_worker_service_name" {
  description = "ECS Celery worker service name"
  value       = aws_ecs_service.celery_worker.name
}

output "api_url" {
  description = "API URL (from ALB or service)"
  value       = var.target_group_arn != "" ? "http://${replace(var.target_group_arn, ".*targetgroup/(.*)/.*", "$1")}" : ""
}
