# TradeSeekerWeb v2 - Deployment Guide

This guide covers deploying the TradeSeekerWeb v2 application to AWS S3 with CloudFront CDN.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed (>= 1.0)
- Node.js and npm installed
- S3 bucket `ts-web-v2-terraform-state` for Terraform state (already configured)

## Step 1: Configure Terraform Variables

Create a `terraform.tfvars` file in the `terraform/` directory:

```hcl
bucket_name = "your-unique-bucket-name"
project_name = "tradeseeker-web-v2"
environment = "prod"
aws_region = "ap-southeast-1"
```

## Step 2: Deploy Infrastructure

The Terraform state is stored remotely in S3 bucket `ts-web-v2-terraform-state`.

```bash
cd terraform

# Initialize Terraform (will configure remote state)
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply

# Note the outputs:
# - s3_bucket_name
# - cloudfront_distribution_id
# - website_url
```

## Step 3: Build the Application

```bash
cd ..
./scripts/build.sh
```

This will:
- Install dependencies with `npm ci`
- Build the production bundle
- Output to `dist/tradeseeker-web-v2/browser/`

## Step 4: Deploy to S3

```bash
./scripts/deploy.sh <s3-bucket-name> <cloudfront-distribution-id>
```

Example:
```bash
./scripts/deploy.sh my-tradeseeker-bucket E1234567890ABC
```

This will:
- Upload all files to S3
- Set appropriate cache headers
- Invalidate CloudFront cache

## Step 5: Access Your Application

Your application will be available at the CloudFront URL provided in the Terraform outputs:

```
https://d1234567890abc.cloudfront.net
```

## Updating the Application

After making changes:

1. Build: `./scripts/build.sh`
2. Deploy: `./scripts/deploy.sh <bucket-name> <distribution-id>`

Or just invalidate cache:
```bash
./scripts/invalidate-cache.sh <distribution-id>
```

## Environment Configuration

Update `src/environments/environment.prod.ts` with your production settings:

```typescript
export const environment = {
  production: true,
  apiBaseUrl: 'https://your-api-url.com',
  cognito: {
    userPoolId: 'your-user-pool-id',
    clientId: 'your-client-id',
    region: 'ap-southeast-1'
  }
};
```

## Troubleshooting

### CloudFront takes time to update
- Cache invalidation can take 5-15 minutes
- Use `index.html` with no-cache headers for faster updates

### 403/404 errors on refresh
- Ensure CloudFront custom error responses are configured
- Check that `index.html` is set as error document

### Authentication issues
- Verify Cognito configuration in environment files
- Check that Cognito app client allows the CloudFront domain

## Cost Optimization

- CloudFront: ~$0.085/GB for first 10TB
- S3: ~$0.023/GB storage + $0.09/GB transfer
- Estimated cost for low traffic: $5-10/month

## Security Best Practices

1. Enable CloudFront access logging
2. Use AWS WAF for additional protection
3. Implement custom domain with SSL certificate
4. Rotate Cognito credentials regularly
5. Review S3 bucket policies

## Custom Domain (Optional)

To use a custom domain:

1. Request SSL certificate in ACM (us-east-1 region)
2. Update CloudFront distribution with custom domain
3. Add CNAME record in your DNS provider

## Monitoring

- CloudFront metrics in CloudWatch
- S3 access logs
- Cognito authentication metrics
- API Gateway logs for backend calls
