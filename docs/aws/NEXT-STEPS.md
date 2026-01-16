# Next Steps - Your Deployment is Complete! 🎉

## Current Status

✅ **Infrastructure Deployed**: All AWS resources are created successfully  
⚠️ **API Status**: 503 (tasks still starting - this is normal!)  
⏳ **Wait Time**: ECS tasks take 1-2 minutes to start and become healthy

---

## Immediate Actions

### 1. Wait for ECS Tasks to Start (1-2 minutes)

ECS tasks are starting up. Check their status:

```bash
# Check service status
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api \
  --region eu-west-1 \
  --profile fastship \
  --query 'services[0].{DesiredCount:desiredCount,RunningCount:runningCount,Status:status}'

# Expected output after 1-2 minutes:
# {
#   "DesiredCount": 1,
#   "RunningCount": 1,
#   "Status": "ACTIVE"
# }
```

### 2. Monitor ECS Logs

Watch the logs in real-time to see startup progress:

```bash
# View API startup logs
aws logs tail /ecs/dev-api --follow --region eu-west-1 --profile fastship
```

**Look for**:
- ✅ "Starting application on port 8000..."
- ✅ "✅ Database connection successful"
- ✅ "✅ Redis connection successful"
- ✅ "Application startup checks complete"

### 3. Check Target Health

Once tasks are running, check if ALB can reach them:

```bash
# Get target group name
TG_ARN=$(aws elbv2 describe-target-groups \
  --region eu-west-1 \
  --profile fastship \
  --query 'TargetGroups[?contains(TargetGroupName, `fastship-dev-backend`)].TargetGroupArn' \
  --output text)

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn ${TG_ARN} \
  --region eu-west-1 \
  --profile fastship \
  --query 'TargetHealthDescriptions[*].{Target:Target.Id,Health:TargetHealth.State,Reason:TargetHealth.Reason}'
```

**Wait for**: Targets to show `healthy` state (may take 2-3 minutes)

### 4. Test API Once Healthy

Once targets are healthy, test the API:

```bash
# Health check
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health

# Expected response:
# {"status":"healthy","redis":"connected","service":"FastAPI Backend"}
```

---

## Quick Verification Commands

```bash
# 1. Check ECS services
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api dev-celery-worker \
  --region eu-west-1 \
  --profile fastship \
  --query 'services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount,Status:status}'

# 2. View recent logs
aws logs tail /ecs/dev-api --since 5m --region eu-west-1 --profile fastship

# 3. Test API (after tasks are healthy)
curl -v http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health

# 4. Check task status
aws ecs list-tasks \
  --cluster dev-fastship-cluster \
  --service-name dev-api \
  --region eu-west-1 \
  --profile fastship
```

---

## What to Expect

### Normal Startup Sequence (2-3 minutes)

1. **0-30 seconds**: ECS tasks start pulling Docker image
2. **30-60 seconds**: Container starts, application begins startup
3. **60-90 seconds**: Database connection established
4. **90-120 seconds**: Redis connection established
5. **120-180 seconds**: Health check passes, ALB marks target as healthy

### Common Issues

**503 Service Unavailable**:
- ⏳ Normal during first 1-2 minutes
- ✅ Should resolve once tasks are healthy

**Tasks not starting**:
- Check ECS logs for errors
- Verify Docker image exists in ECR
- Check task definition configuration

**Database connection errors**:
- Verify security group allows ECS → RDS
- Check database credentials in task environment variables

---

## Your Deployment URLs

```
API Endpoints:
- Health: http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health
- Docs: http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/docs
- Scalar: http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/scalar

Frontend:
- CloudFront: https://ddx58afhk5dnp.cloudfront.net

Infrastructure:
- ECS Cluster: dev-fastship-cluster
- RDS: fastship-dev-db.ct4i6mg6a7a1.eu-west-1.rds.amazonaws.com
- Redis: master.fastship-dev-redis.ktchac.euw1.cache.amazonaws.com
```

---

## After API is Healthy - Next Steps

### 1. Deploy Frontend

```bash
cd /home/angelo/proyectos/cursos/fastship-aws
ENV=dev ./infrastructure/scripts/deploy-frontend.sh
```

### 2. Set Up GitHub Actions

1. Add GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `CLOUDFRONT_DISTRIBUTION_ID` (get from Terraform outputs)

2. Push code to trigger workflows

### 3. Configure Monitoring

- Set up CloudWatch alarms
- Create monitoring dashboard
- Configure log aggregation

### 4. Optional Enhancements

- Custom domain setup
- SSL/TLS certificates (HTTPS)
- Auto-scaling configuration
- Backup policies

---

## Need Help?

- See [POST-DEPLOYMENT-VERIFICATION.md](./POST-DEPLOYMENT-VERIFICATION.md) for detailed checks
- Check [DEPLOYMENT-WORKFLOW.md](./DEPLOYMENT-WORKFLOW.md) for deployment steps
- Review CloudWatch logs for error messages

---

**🚀 Your FastShip application is deployed! Wait 1-2 minutes, then test the API!**
