terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "fastship-tf-state-dev"
    key            = "terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "fastship-tf-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  environment = "dev"
}

module "vpc" {
  source = "../../modules/vpc"

  environment          = local.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  enable_nat_gateway   = var.enable_nat_gateway
}

module "rds" {
  source = "../../modules/rds"

  project_name       = "fastship"
  environment        = local.environment
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.networking.rds_security_group_id

  db_name     = var.database_name
  db_username = var.username
  db_password = var.db_password

  instance_class    = var.instance_class
  allocated_storage = var.rds_allocated_storage
}

module "redis" {
  source = "../../modules/redis"

  project_name       = "fastship"
  environment        = local.environment
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.networking.redis_security_group_id

  node_type       = var.node_type
  num_cache_nodes = var.redis_num_cache_nodes
  auth_token      = var.redis_auth_token
}

module "networking" {
  source = "../../modules/networking"

  project_name      = "fastship"
  environment       = local.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

module "ecs" {
  source = "../../modules/ecs"

  project_name          = "fastship"
  environment           = local.environment
  aws_region            = var.aws_region
  backend_image         = var.backend_image
  public_subnet_ids     = module.vpc.public_subnet_ids
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.networking.ecs_security_group_id
  target_group_arn      = module.networking.target_group_arn
  api_use_public_subnets = var.api_use_public_subnets

  api_task_cpu    = var.api_task_cpu
  api_task_memory = var.api_task_memory
  api_desired_count = var.api_desired_count

  worker_task_cpu    = var.worker_task_cpu
  worker_task_memory = var.worker_task_memory
  worker_desired_count = var.worker_desired_count

  log_retention_days = var.log_retention_days

  container_environment = [
    {
      name  = "DATABASE_URL"
      value = "postgresql+asyncpg://${var.username}:${var.db_password}@${module.rds.db_endpoint}/${var.database_name}"
    },
    {
      name  = "REDIS_URL"
      value = "redis://:${var.redis_auth_token}@${module.redis.redis_endpoint}:${module.redis.redis_port}"
    }
  ]
}

module "frontend" {
  source = "../../modules/frontend"

  project_name = "fastship"
  environment  = local.environment
}
