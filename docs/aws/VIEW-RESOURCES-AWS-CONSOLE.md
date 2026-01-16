# How to View FastShip Resources in AWS Console

## Important: Region and Account

All resources are deployed to:
- **Region**: `eu-west-1` (Ireland)
- **Account**: `337573345298`

**⚠️ Make sure you're viewing the correct region in the AWS Console!**

---

## 1. View ECR Repository (Docker Images)

### In AWS Console:

1. Go to **Amazon ECR** service: https://eu-west-1.console.aws.amazon.com/ecr/home?region=eu-west-1#/repositories
2. Make sure region selector shows: **eu-west-1 (Ireland)**
3. You should see repository: **fastship-backend**
4. Click on it to view:
   - Images pushed to the repository
   - Image tags (latest, etc.)
   - Image scanning results

### Via AWS CLI:

```bash
export AWS_PROFILE=fastship

# List repositories
aws ecr describe-repositories --region eu-west-1

# List images in repository
aws ecr list-images --repository-name fastship-backend --region eu-west-1

# View image details
aws ecr describe-images --repository-name fastship-backend --region eu-west-1
```

---

## 2. View ECS Cluster and Services

### In AWS Console:

1. Go to **Amazon ECS** service: https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters?region=eu-west-1
2. Make sure region selector shows: **eu-west-1 (Ireland)**
3. You should see cluster: **dev-fastship-cluster**
4. Click on it to view:
   - **Services** tab: `dev-api` and `dev-celery-worker`
   - **Tasks** tab: Running tasks
   - **Metrics** tab: Cluster performance

### To view service details:

1. Click on **dev-fastship-cluster**
2. Go to **Services** tab
3. Click on **dev-api** to view:
   - Task definition (dev-api:3)
   - Running tasks
   - Service events
   - Health check status
   - Logs (CloudWatch)

### Via AWS CLI:

```bash
export AWS_PROFILE=fastship

# List clusters
aws ecs list-clusters --region eu-west-1

# Describe cluster
aws ecs describe-clusters --clusters dev-fastship-cluster --region eu-west-1

# List services
aws ecs list-services --cluster dev-fastship-cluster --region eu-west-1

# Describe service
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api \
  --region eu-west-1

# List tasks
aws ecs list-tasks --cluster dev-fastship-cluster --service-name dev-api --region eu-west-1

# Describe task
aws ecs describe-tasks \
  --cluster dev-fastship-cluster \
  --tasks <task-arn> \
  --region eu-west-1
```

---

## 3. View Application Load Balancer (ALB)

### In AWS Console:

1. Go to **EC2 → Load Balancers**: https://eu-west-1.console.aws.amazon.com/ec2/home?region=eu-west-1#LoadBalancers:
2. Make sure region shows: **eu-west-1 (Ireland)**
3. You should see: **fastship-dev-alb**
4. Click on it to view:
   - **Target Groups** tab: `fastship-dev-backend-tg`
   - **Listeners** tab: HTTP:80 listener
   - DNS name: `fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com`

### Check target health:

1. Go to **Target Groups**: https://eu-west-1.console.aws.amazon.com/ec2/home?region=eu-west-1#TargetGroups:
2. Click on **fastship-dev-backend-tg**
3. Go to **Targets** tab to see:
   - Target health status
   - Health check response
   - Unhealthy target reasons

### Via AWS CLI:

```bash
export AWS_PROFILE=fastship

# List load balancers
aws elbv2 describe-load-balancers --region eu-west-1

# Describe target group health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:eu-west-1:337573345298:targetgroup/fastship-dev-backend-tg/64d0ef32d1184005 \
  --region eu-west-1
```

---

## 4. View CloudWatch Logs

### In AWS Console:

1. Go to **CloudWatch → Logs**: https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups
2. Make sure region shows: **eu-west-1 (Ireland)**
3. Look for log groups:
   - `/ecs/dev-api` (API service logs)
   - `/ecs/dev-celery-worker` (Celery worker logs)
4. Click on a log group to view streams and logs

### Via AWS CLI:

```bash
export AWS_PROFILE=fastship

# List log groups
aws logs describe-log-groups --region eu-west-1 --query 'logGroups[?contains(logGroupName, `ecs`)].logGroupName' --output table

# Tail logs
aws logs tail /ecs/dev-api --follow --region eu-west-1

# View recent logs (last 10 minutes)
aws logs tail /ecs/dev-api --since 10m --region eu-west-1
```

---

## 5. View RDS Database

### In AWS Console:

1. Go to **Amazon RDS**: https://eu-west-1.console.aws.amazon.com/rds/home?region=eu-west-1#databases:
2. Make sure region shows: **eu-west-1 (Ireland)**
3. You should see: **fastship-dev-db**
4. Click on it to view:
   - Endpoint: `fastship-dev-db.ct4i6mg6a7a1.eu-west-1.rds.amazonaws.com`
   - Status
   - Security groups
   - Connection details

### Via AWS CLI:

```bash
export AWS_PROFILE=fastship

# List databases
aws rds describe-db-instances --region eu-west-1 --query 'DBInstances[*].{Name:DBInstanceIdentifier,Status:DBInstanceStatus,Endpoint:Endpoint.Address}' --output table
```

---

## 6. View ElastiCache Redis

### In AWS Console:

1. Go to **Amazon ElastiCache**: https://eu-west-1.console.aws.amazon.com/elasticache/home?region=eu-west-1#/redis
2. Make sure region shows: **eu-west-1 (Ireland)**
3. You should see: **fastship-dev-redis**
4. Click on it to view:
   - Endpoint
   - Status
   - Configuration

### Via AWS CLI:

```bash
export AWS_PROFILE=fastship

# List Redis clusters
aws elasticache describe-replication-groups --region eu-west-1 --query 'ReplicationGroups[*].{Name:ReplicationGroupId,Status:Status,Endpoint:NodeGroups[0].PrimaryEndpoint.Address}' --output table
```

---

## Quick Links (eu-west-1)

- **ECR**: https://eu-west-1.console.aws.amazon.com/ecr/home?region=eu-west-1#/repositories
- **ECS**: https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters?region=eu-west-1
- **ALB**: https://eu-west-1.console.aws.amazon.com/ec2/home?region=eu-west-1#LoadBalancers:
- **CloudWatch Logs**: https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups
- **RDS**: https://eu-west-1.console.aws.amazon.com/rds/home?region=eu-west-1#databases:
- **ElastiCache**: https://eu-west-1.console.aws.amazon.com/elasticache/home?region=eu-west-1#/redis

---

## Troubleshooting: If You Don't See Resources

1. **Check Region**: Make sure you're viewing **eu-west-1 (Ireland)** in the AWS Console
2. **Check Account**: Verify you're logged into account **337573345298**
3. **Check IAM Permissions**: Ensure your AWS profile has necessary permissions
4. **Verify with CLI**: Use AWS CLI commands above to verify resources exist

---

## Debugging 504 Errors

If you're getting 504 errors:

1. **Check ALB Target Health**:
   - Go to EC2 → Target Groups → fastship-dev-backend-tg
   - Check if targets are healthy
   - If unhealthy, check reason

2. **Check ECS Task Logs**:
   - Go to CloudWatch → Logs → /ecs/dev-api
   - Look for errors in recent logs

3. **Check ECS Service Events**:
   - Go to ECS → Clusters → dev-fastship-cluster → Services → dev-api
   - View service events for error messages

4. **Check Task Status**:
   - Go to ECS → Clusters → dev-fastship-cluster → Tasks
   - Check if tasks are running or stopped
   - View stopped task reasons
