# Rebuild and Redeploy Docker Image

## Quick Reference - ECR Repository URI

```
ECR Repository: 337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend
```

## Step-by-Step Commands

### 1. Login to ECR

```bash
aws ecr get-login-password --region eu-west-1 --profile fastship | \
  docker login --username AWS --password-stdin 337573345298.dkr.ecr.eu-west-1.amazonaws.com
```

**Note**: Use the repository URI **without** the repository name (`/fastship-backend`) for the login server.

### 2. Build Docker Image

```bash
cd /home/angelo/proyectos/cursos/fastship-aws/src/backend
docker build -t fastship-backend:latest .
```

### 3. Tag for ECR

```bash
docker tag fastship-backend:latest 337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend:latest
```

### 4. Push to ECR

```bash
docker push 337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend:latest
```

### 5. Force ECS Deployment

```bash
aws ecs update-service \
  --cluster dev-fastship-cluster \
  --service dev-api \
  --force-new-deployment \
  --region eu-west-1 \
  --profile fastship
```

### 6. Monitor Deployment

```bash
# Watch logs
aws logs tail /ecs/dev-api --follow --region eu-west-1 --profile fastship

# Check service status
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api \
  --region eu-west-1 \
  --profile fastship \
  --query 'services[0].{RunningCount:runningCount,Status:status}'
```

### 7. Test API

Wait 2-3 minutes, then:
```bash
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health
```

---

## All-in-One Script

```bash
#!/bin/bash
set -e

ECR_REGISTRY="337573345298.dkr.ecr.eu-west-1.amazonaws.com"
ECR_REPO="fastship-backend"
ECR_URI="${ECR_REGISTRY}/${ECR_REPO}"

echo "1. Logging in to ECR..."
aws ecr get-login-password --region eu-west-1 --profile fastship | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo "2. Building Docker image..."
cd /home/angelo/proyectos/cursos/fastship-aws/src/backend
docker build -t fastship-backend:latest .

echo "3. Tagging image..."
docker tag fastship-backend:latest ${ECR_URI}:latest

echo "4. Pushing to ECR..."
docker push ${ECR_URI}:latest

echo "5. Forcing ECS deployment..."
aws ecs update-service \
  --cluster dev-fastship-cluster \
  --service dev-api \
  --force-new-deployment \
  --region eu-west-1 \
  --profile fastship \
  --query 'service.{ServiceName:serviceName,Status:status}' \
  --output json

echo ""
echo "✅ Deployment initiated!"
echo "Wait 2-3 minutes, then test:"
echo "curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health"
```

Save as `rebuild-deploy.sh` and run: `chmod +x rebuild-deploy.sh && ./rebuild-deploy.sh`
