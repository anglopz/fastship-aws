terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "fastship-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  project_name = "fastship"
  environment  = "prod"
}

module "vpc" {
  source = "../../modules/vpc"

  project_name         = local.project_name
  environment          = local.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "networking" {
  source = "../../modules/networking"

  project_name      = local.project_name
  environment       = local.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

module "rds" {
  source = "../../modules/rds"

  project_name       = local.project_name
  environment        = local.environment
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.networking.rds_security_group_id

  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password

  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  backup_retention_period = var.rds_backup_retention_period
  performance_insights_enabled = true
}

module "redis" {
  source = "../../modules/redis"

  project_name       = local.project_name
  environment        = local.environment
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.networking.redis_security_group_id

  auth_token      = var.redis_auth_token
  node_type       = var.redis_node_type
  num_cache_nodes = var.redis_num_cache_nodes
  snapshot_retention_limit = var.redis_snapshot_retention_limit
}

module "ecs" {
  source = "../../modules/ecs"

  project_name          = local.project_name
  environment           = local.environment
  aws_region            = var.aws_region
  backend_image         = var.backend_image
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.networking.ecs_security_group_id
  target_group_arn      = module.networking.target_group_arn

  task_cpu       = var.task_cpu
  task_memory    = var.task_memory
  desired_count  = var.desired_count
  log_retention_days = var.log_retention_days

  container_environment = [
    {
      name  = "DATABASE_URL"
      value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
    },
    {
      name  = "REDIS_URL"
      value = "redis://:${var.redis_auth_token}@${module.redis.redis_endpoint}:${module.redis.redis_port}"
    }
  ]
}

module "frontend" {
  source = "../../modules/frontend"

  project_name = local.project_name
  environment  = local.environment
}
