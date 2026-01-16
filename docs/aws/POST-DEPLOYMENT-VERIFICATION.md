# Post-Deployment Verification Guide

## ✅ Deployment Complete!

Your FastShip infrastructure is now deployed to AWS. Here's how to verify everything is working correctly.

## Quick Reference - Your Deployment URLs

```
API URL: http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com
CloudFront: ddx58afhk5dnp.cloudfront.net
ECS Cluster: dev-fastship-cluster
ECS Services: dev-api, dev-celery-worker
RDS Endpoint: fastship-dev-db.ct4i6mg6a7a1.eu-west-1.rds.amazonaws.com:5432
Redis Endpoint: master.fastship-dev-redis.ktchac.euw1.cache.amazonaws.com
ECR Repository: 337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend
```

---

## 1. Verify ECS Services

### Check Service Status

```bash
# Check API service
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api \
  --region eu-west-1 \
  --profile fastship \
  --query 'services[0].{ServiceName:serviceName,DesiredCount:desiredCount,RunningCount:runningCount,Status:status}'

# Check Celery worker service
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-celery-worker \
  --region eu-west-1 \
  --profile fastship \
  --query 'services[0].{ServiceName:serviceName,DesiredCount:desiredCount,RunningCount:runningCount,Status:status}'
```

**Expected Output**:
- `runningCount` should equal `desiredCount` (1)
- `status` should be `ACTIVE`

### List Running Tasks

```bash
# List API tasks
aws ecs list-tasks \
  --cluster dev-fastship-cluster \
  --service-name dev-api \
  --region eu-west-1 \
  --profile fastship

# Get task details (use task ARN from above)
aws ecs describe-tasks \
  --cluster dev-fastship-cluster \
  --tasks <TASK_ARN> \
  --region eu-west-1 \
  --profile fastship \
  --query 'tasks[0].{LastStatus:lastStatus,HealthStatus:healthStatus,Containers:containers[*].{Name:name,Status:lastStatus}}'
```

**Expected**: Tasks should be `RUNNING` with `HEALTHY` status.

---

## 2. Test API Endpoints

### Health Check

```bash
# Test health endpoint
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health

# Expected response:
# {"status":"healthy","redis":"connected","service":"FastAPI Backend"}
```

### API Documentation

```bash
# Open in browser or curl:
# Swagger UI
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/docs

# Scalar Docs
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/scalar
```

### Test Redis Cache Endpoint

```bash
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/test-redis

# Expected: {"success":true,"message":"Redis is working correctly",...}
```

---

## 3. Check ECS Task Logs

### View API Logs

```bash
# Follow logs in real-time
aws logs tail /ecs/dev-api --follow --region eu-west-1 --profile fastship

# Or view last 100 lines
aws logs tail /ecs/dev-api --since 10m --region eu-west-1 --profile fastship
```

**Look for**:
- ✅ "Application startup checks complete"
- ✅ "Connected to Redis (cache)"
- ✅ "Database connection successful"
- ❌ No error messages

### View Celery Worker Logs

```bash
aws logs tail /ecs/dev-celery-worker --follow --region eu-west-1 --profile fastship
```

**Look for**:
- ✅ Celery worker started
- ✅ Connected to Redis broker
- ❌ No connection errors

---

## 4. Verify Database Connectivity

### Test from Local Machine (if database is accessible)

```bash
# Test RDS connectivity (if security groups allow)
psql -h fastship-dev-db.ct4i6mg6a7a1.eu-west-1.rds.amazonaws.com \
  -p 5432 \
  -U fastship \
  -d fastship
```

### Check Database from ECS Task

The application logs should show:
- ✅ "Database connection successful"
- ✅ "Database tables created/verified"

If you see database connection errors in ECS logs:
1. Check security group allows traffic from ECS security group
2. Verify database credentials in ECS task environment variables

---

## 5. Verify Load Balancer Health

### Check Target Group Health

```bash
# Get target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --region eu-west-1 \
  --profile fastship \
  --query 'TargetGroups[?contains(TargetGroupName, `fastship-dev-backend`)].TargetGroupArn' \
  --output text)

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn ${TG_ARN} \
  --region eu-west-1 \
  --profile fastship
```

**Expected**: Targets should be `healthy`.

---

## 6. Test Frontend (CloudFront)

```bash
# Test CloudFront distribution
curl https://ddx58afhk5dnp.cloudfront.net

# Or open in browser:
# https://ddx58afhk5dnp.cloudfront.net
```

**Note**: Frontend may not be deployed yet if you haven't run the frontend deployment script.

---

## 7. Performance Checks

### Response Time

```bash
# Test API response time
time curl -w "\nTime: %{time_total}s\n" \
  http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health
```

**Expected**: < 1 second for health check

### Check Cache Headers

```bash
# Test caching (should see X-Cache header)
curl -I http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/api/v1/health

# First request: X-Cache: MISS
# Second request: X-Cache: HIT (if caching is working)
```

---

## 8. Security Verification

### Check Security Groups

```bash
# List security groups
aws ec2 describe-security-groups \
  --region eu-west-1 \
  --profile fastship \
  --query 'SecurityGroups[?contains(GroupName, `fastship-dev`)].{Name:GroupName,Ingress:IpPermissions}'
```

**Verify**:
- ALB allows HTTP (80) and HTTPS (443) from internet
- ECS only allows traffic from ALB security group
- RDS only allows traffic from ECS security group
- Redis only allows traffic from ECS security group

### Check Encryption

```bash
# RDS encryption
aws rds describe-db-instances \
  --db-instance-identifier fastship-dev-db \
  --region eu-west-1 \
  --profile fastship \
  --query 'DBInstances[0].StorageEncrypted'

# ECR encryption
aws ecr describe-repositories \
  --repository-names fastship-backend \
  --region eu-west-1 \
  --profile fastship \
  --query 'repositories[0].EncryptionConfiguration'
```

---

## 9. Cost Monitoring

### Check Current Costs

```bash
# Estimate daily cost (free tier eligible)
# RDS: $0 (free tier first 12 months)
# Redis: $0 (free tier first 12 months)
# ECS Fargate: ~$0.04/day (256 CPU, 512 MB) = ~$1.20/month
# ALB: ~$0.54/day = ~$16.20/month
# Data Transfer: Varies

# Total estimated: ~$17-20/month (mostly ALB)
```

### Set Up Billing Alerts

1. Go to AWS Billing Console
2. Create budget alert for $25/month
3. Set notifications at 80% ($20)

---

## 10. Next Steps

### Immediate Actions

1. ✅ **Verify all services are running** (see above)
2. ✅ **Test API endpoints** (health check works)
3. ✅ **Monitor CloudWatch logs** for any errors
4. ⏭️ **Deploy frontend** (if not done yet)
5. ⏭️ **Configure custom domain** (optional)

### Future Enhancements

1. **Set up CloudWatch Alarms**:
   - ECS service health
   - API response time
   - Error rate thresholds

2. **Configure Auto Scaling**:
   - Scale ECS tasks based on CPU/memory
   - Scale based on ALB request count

3. **Set up Monitoring Dashboard**:
   - CloudWatch Dashboard
   - ECS service metrics
   - API performance metrics

4. **CI/CD Pipeline**:
   - GitHub Actions for automated deployments
   - Automated testing before deployment

5. **Backup Configuration**:
   - RDS automated backups (already configured)
   - Database snapshot schedule

6. **Security Hardening**:
   - Enable AWS WAF on ALB
   - Set up AWS Shield (basic included)
   - Configure SSL/TLS certificates (HTTPS)

---

## Troubleshooting

### ECS Service Not Starting

```bash
# Check service events
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api \
  --region eu-west-1 \
  --profile fastship \
  --query 'services[0].events[:5]'
```

### Tasks Failing to Start

```bash
# Get task stop reason
aws ecs describe-tasks \
  --cluster dev-fastship-cluster \
  --tasks <TASK_ARN> \
  --region eu-west-1 \
  --profile fastship \
  --query 'tasks[0].stoppedReason'
```

### Database Connection Issues

1. Check ECS task security group has access to RDS
2. Verify database credentials in task definition
3. Check RDS security group allows inbound from ECS SG

### API Not Responding

1. Check ALB target health (should be healthy)
2. Verify ECS tasks are running
3. Check ECS task logs for errors
4. Test direct connection to ECS task IP (if in public subnet)

---

## Quick Commands Reference

```bash
# Get all outputs
cd infrastructure/terraform/environments/dev
terraform output

# View ECS logs
aws logs tail /ecs/dev-api --follow --region eu-west-1 --profile fastship

# Check ECS service status
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api dev-celery-worker \
  --region eu-west-1 \
  --profile fastship

# Restart ECS service (force new deployment)
aws ecs update-service \
  --cluster dev-fastship-cluster \
  --service dev-api \
  --force-new-deployment \
  --region eu-west-1 \
  --profile fastship

# Test API
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health
```

---

## Success Criteria

✅ **Deployment is successful when**:

1. ✅ ECS services show `runningCount == desiredCount`
2. ✅ API health endpoint returns 200 OK
3. ✅ ECS logs show no errors
4. ✅ ALB target health is healthy
5. ✅ Database connection successful (logs confirm)
6. ✅ Redis connection successful (logs confirm)

---

**Congratulations! Your FastShip application is now deployed on AWS! 🚀**

For more details, see [DEPLOYMENT-AWS.md](./DEPLOYMENT-AWS.md) and [DEPLOYMENT-WORKFLOW.md](./DEPLOYMENT-WORKFLOW.md).
