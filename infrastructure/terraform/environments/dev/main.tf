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

  instance_class          = var.instance_class
  allocated_storage       = var.rds_allocated_storage
  backup_retention_period = var.backup_retention_period
  engine_version          = var.engine_version
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

  project_name        = "fastship"
  environment         = local.environment
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  acm_certificate_arn = var.acm_certificate_arn
}

module "ecr" {
  source = "../../modules/ecr"

  project_name = "fastship"
  environment  = local.environment
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
    # Use individual POSTGRES_* variables instead of DATABASE_URL to avoid URL encoding issues
    # This prevents Python ConfigParser from interpreting special characters (% in password) as interpolation
    # The app's DatabaseSettings will construct the URL from these individual settings
    {
      name  = "POSTGRES_SERVER"
      value = module.rds.db_address
    },
    {
      name  = "POSTGRES_PORT"
      value = tostring(module.rds.db_port)
    },
    {
      name  = "POSTGRES_USER"
      value = var.username
    },
    {
      name  = "POSTGRES_PASSWORD"
      value = var.db_password
    },
    {
      name  = "POSTGRES_DB"
      value = var.database_name
    },
    # Redis URL (no special characters in auth token, so safe to use URL)
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
