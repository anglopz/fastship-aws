.PHONY: help install build push deploy-infra deploy-all dev dev-backend dev-frontend test clean terraform-init terraform-plan terraform-apply deploy-terraform deploy-backend deploy-frontend

# Default target
help:
	@echo "FastShip AWS - Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install all dependencies"
	@echo "  make dev              - Start all services locally"
	@echo "  make dev-backend      - Start backend only"
	@echo "  make dev-frontend     - Start frontend only"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Run backend tests"
	@echo "  make test-frontend    - Run frontend tests"
	@echo ""
	@echo "Build & Push:"
	@echo "  make build            - Build Docker images"
	@echo "  make push [ENV=dev]   - Build and push to ECR"
	@echo ""
	@echo "Terraform:"
	@echo "  make terraform-init [ENV=dev]    - Initialize Terraform"
	@echo "  make terraform-plan [ENV=dev]    - Plan Terraform changes"
	@echo "  make terraform-apply [ENV=dev]   - Apply Terraform changes"
	@echo ""
	@echo "AWS Deployment:"
	@echo "  make deploy-terraform [ENV=dev]  - Full Terraform deployment (init+plan+apply)"
	@echo "  make deploy-backend [ENV=dev]    - Build and deploy backend to ECS"
	@echo "  make deploy-frontend [ENV=dev]   - Build and deploy frontend to S3"
	@echo "  make deploy-all [ENV=dev]        - Full deployment (terraform+build+push)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            - Clean build artifacts"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd src/backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd src/frontend && npm install

# Development
dev:
	docker-compose -f src/backend/docker-compose.yml up -d

dev-backend:
	cd src/backend && docker-compose up -d

dev-frontend:
	cd src/frontend && npm run dev

# Testing
test: test-backend test-frontend

test-backend:
	cd src/backend && pytest

test-frontend:
	cd src/frontend && npm test || echo "No tests configured"

# Build
build:
	@echo "Building Docker images with docker-compose..."
	docker-compose -f docker-compose.aws.yml build

# Clean
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".vite" -exec rm -r {} + 2>/dev/null || true

# Terraform commands
terraform-init:
	@ENV=$${ENV:-dev}; \
	echo "Initializing Terraform for $$ENV environment..."; \
	cd infrastructure/terraform/environments/$$ENV && terraform init

terraform-plan:
	@ENV=$${ENV:-dev}; \
	echo "Planning Terraform changes for $$ENV environment..."; \
	cd infrastructure/terraform/environments/$$ENV && terraform plan -var-file=terraform.tfvars

terraform-apply:
	@ENV=$${ENV:-dev}; \
	echo "Applying Terraform changes for $$ENV environment..."; \
	cd infrastructure/terraform/environments/$$ENV && terraform apply -auto-approve -var-file=terraform.tfvars

# Terraform deployment (full workflow)
deploy-terraform: terraform-init terraform-plan terraform-apply

# Backend deployment
deploy-backend:
	@ENV=$${ENV:-dev}; \
	echo "Building and deploying backend to $$ENV environment..."; \
	./infrastructure/scripts/build-and-push.sh $$ENV && \
	IMAGE_URI=$$(aws ecr describe-images --repository-name fastship-backend --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' --output text | xargs -I {} echo $$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$${AWS_REGION:-us-east-1}.amazonaws.com/fastship-backend:{}) && \
	./infrastructure/scripts/deploy-backend.sh $$ENV $$IMAGE_URI

# Push to ECR
push:
	@ENV=$${ENV:-dev}; \
	echo "Building and pushing Docker images to ECR for $$ENV environment..."; \
	./infrastructure/scripts/build-and-push.sh $$ENV

# Frontend deployment
deploy-frontend:
	@ENV=$${ENV:-dev}; \
	echo "Building and deploying frontend to $$ENV environment..."; \
	./infrastructure/scripts/deploy-frontend.sh $$ENV

# Full deployment workflow
deploy-all: terraform-init terraform-apply build push
	@echo "Full deployment completed!"

# AWS simulation (local testing with AWS-like setup)
dev-aws:
	docker-compose -f docker-compose.aws.yml up -d

# Terraform validation
terraform-validate:
	@echo "Validating Terraform configuration..."
	cd infrastructure/terraform && terraform init -backend=false && terraform validate
	@ENV=$${ENV:-dev}; \
	echo "Validating $$ENV environment..."; \
	cd infrastructure/terraform/environments/$$ENV && terraform init -backend=false && terraform validate

# Terraform format
terraform-fmt:
	@echo "Formatting Terraform files..."
	terraform fmt -recursive infrastructure/terraform
