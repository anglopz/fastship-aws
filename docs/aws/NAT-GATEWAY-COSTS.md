# NAT Gateway Costs and Free Tier Options

## ⚠️ Important: NAT Gateway Charges

**NAT Gateway is NOT included in AWS Free Tier** and will incur charges even on trial accounts:

- **Cost**: ~$0.045/hour + data transfer charges
- **Monthly cost**: ~$32/month if running 24/7 (just for the NAT Gateway)
- **Data transfer**: Additional charges for data processed through NAT Gateway

## Free Tier Solution: Disable NAT Gateway for Dev

For a truly free-tier dev environment, we've made NAT Gateway **optional**.

### Current Configuration (Free Tier)

In `../../infrastructure/terraform/environments/dev/terraform.tfvars`:
```hcl
enable_nat_gateway = false  # Free tier - no NAT Gateway costs
```

### What This Means

**Without NAT Gateway:**
- ✅ **Public subnets**: Full internet access (free)
- ✅ **ECS tasks in public subnets**: Can access internet, ECR, external APIs
- ⚠️ **Private subnets**: No internet access
- ⚠️ **RDS/Redis in private subnets**: Cannot access internet (but this is usually fine - they don't need it)

### Architecture Options

#### Option 1: Free Tier (No NAT Gateway) - RECOMMENDED FOR DEV

```
Public Subnets:
  - ECS API Service (with public IP)
  - ALB (load balancer)
  
Private Subnets:
  - RDS (no internet needed)
  - Redis (no internet needed)
  - ECS Celery Worker (can use public subnets if needed)
```

**Pros:**
- ✅ Zero NAT Gateway costs
- ✅ RDS/Redis still secure in private subnets
- ✅ ECS can access ECR and internet from public subnets

**Cons:**
- ⚠️ ECS tasks have public IPs (but protected by security groups)
- ⚠️ Celery worker might need public subnet if it needs internet access

#### Option 2: With NAT Gateway (Production-like)

```hcl
# In infrastructure/terraform/environments/dev/terraform.tfvars
enable_nat_gateway = true  # Costs ~$32/month
```

**Pros:**
- ✅ All resources in private subnets
- ✅ More secure (no public IPs on ECS tasks)
- ✅ Production-like architecture

**Cons:**
- ❌ Costs ~$32/month for NAT Gateway
- ❌ Additional data transfer charges

## Security Considerations

### Without NAT Gateway

**Security is still maintained through:**
1. **Security Groups**: Control inbound/outbound traffic
2. **Private Subnets**: RDS and Redis are not directly accessible from internet
3. **ALB**: Only the load balancer is publicly accessible
4. **Network ACLs**: Additional layer of security (optional)

**ECS in Public Subnets:**
- Tasks get public IPs but are protected by security groups
- Only port 8000 (or configured ports) are accessible
- Inbound traffic is controlled by security group rules

### Best Practice for Dev

For development/testing, **Option 1 (no NAT Gateway)** is recommended:
- Saves ~$32/month
- Still secure with proper security groups
- RDS/Redis remain in private subnets (protected)
- ECS can function normally in public subnets

## Configuration

### Enable NAT Gateway (Production-like)

```hcl
# In terraform.tfvars
enable_nat_gateway = true
```

### Disable NAT Gateway (Free Tier)

```hcl
# In infrastructure/terraform/environments/dev/terraform.tfvars
enable_nat_gateway = false
```

## Cost Comparison

| Configuration | NAT Gateway Cost | Monthly Total (24/7) |
|--------------|------------------|---------------------|
| **Free Tier (no NAT)** | $0 | ~$0 |
| **With NAT Gateway** | ~$32 | ~$32+ |

**Note**: Other AWS services (RDS, ECS, etc.) have their own costs, but NAT Gateway is an additional ~$32/month.

## Recommendations

1. **Dev Environment**: Use `enable_nat_gateway = false` (free tier)
2. **Production**: Use `enable_nat_gateway = true` (more secure)
3. **Testing**: Start with NAT disabled, enable if needed

## Troubleshooting

### Issue: ECS tasks can't pull images from ECR

**Solution**: Ensure ECS tasks are in public subnets with `assign_public_ip = true`, or enable NAT Gateway.

### Issue: RDS/Redis can't be reached

**Solution**: Check security groups. RDS/Redis don't need internet access - they just need to be reachable from ECS via security groups.

### Issue: Celery worker needs internet access

**Solution**: Either:
1. Put Celery worker in public subnets, or
2. Enable NAT Gateway

## Summary

✅ **For free-tier dev**: Set `enable_nat_gateway = false` in `infrastructure/terraform/environments/dev/terraform.tfvars`
✅ **Security maintained**: Through security groups and private subnets for RDS/Redis
✅ **Cost savings**: ~$32/month by disabling NAT Gateway
✅ **Production**: Enable NAT Gateway for better security posture
