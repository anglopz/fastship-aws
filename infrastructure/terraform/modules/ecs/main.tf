resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-fastship-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.environment}-fastship-cluster"
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_task_cpu
  memory                   = var.api_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "api"
    image     = var.backend_image
    essential = true  # Mark container as essential to ensure proper port binding

    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]

    # Container health check for ECS
    # This helps ECS determine container health independently of ALB health checks
    # Industry standard: Start period should cover initialization time (migrations, DB connections)
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30  # Check every 30 seconds
      timeout     = 10  # Increased from 5 to 10 seconds (per Amazon Q recommendation)
      retries     = 5   # Increased from 3 to 5 (per Amazon Q recommendation for more tolerance)
      # Start period: 120 seconds grace period for app initialization
      # - During this period, failed checks don't count toward unhealthy status
      # - Allows time for: database migrations, connection establishment, app warmup
      # - Aligned with service health check grace period (300s) for consistency
      startPeriod = 120
    }

    environment = var.container_environment

    secrets = var.container_secrets

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  tags = {
    Name = "${var.environment}-api-task"
  }
}

resource "aws_ecs_task_definition" "celery_worker" {
  family                   = "${var.environment}-celery-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_task_cpu
  memory                   = var.worker_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "celery-worker"
    image = var.backend_image
    command = ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]

    environment = var.container_environment

    secrets = var.container_secrets

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.celery_worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  tags = {
    Name = "${var.environment}-celery-worker-task"
  }
}

resource "aws_ecs_service" "api" {
  name            = "${var.environment}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.api_use_public_subnets ? var.public_subnet_ids : var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = var.api_use_public_subnets
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  # Health check grace period: 300 seconds (5 minutes)
  # Industry standard: Allows time for application initialization before ALB health checks start counting
  # - Prevents premature task termination during startup
  # - Gives app time to complete migrations, DB connections, and warmup
  # - Aligned with container health check start period (120s) + buffer
  health_check_grace_period_seconds = 300

  depends_on = [aws_iam_role_policy_attachment.ecs_execution]
}

resource "aws_ecs_service" "celery_worker" {
  name            = "${var.environment}-celery-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.celery_worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  depends_on = [aws_iam_role_policy_attachment.ecs_execution]
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.environment}-api"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.environment}-api-logs"
  }
}

resource "aws_cloudwatch_log_group" "celery_worker" {
  name              = "/ecs/${var.environment}-celery-worker"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.environment}-celery-worker-logs"
  }
}

resource "aws_iam_role" "ecs_execution" {
  name = "${var.environment}-fastship-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.environment}-fastship-ecs-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "${var.environment}-fastship-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.environment}-fastship-ecs-task-role"
  }
}

# IAM policy for ECS Exec (SSM Session Manager)
# Required for aws ecs execute-command to work
resource "aws_iam_role_policy" "ecs_task_exec" {
  name = "${var.environment}-fastship-ecs-task-exec-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      }
    ]
  })
}
