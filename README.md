# Portfolio Infrastructure (AWS CDK)

This repository contains the infrastructure as code (IaC) configuration for deploying a static portfolio website on AWS, using the AWS Cloud Development Kit (CDK) in Python.

## Overview

This CDK application provisions the following resources:

- **Amazon S3 Bucket** – Configured for static website hosting
- **Amazon CloudFront Distribution** – Enables HTTPS, global content delivery, and automatic redirect to HTTPS
- **Asset Deployment** – Deploys static assets to S3 and manages CloudFront cache invalidation
- **CI/CD Pipeline** – GitHub Actions workflow automates deployment on push to the `main` branch

## Stack Configuration

- **Stack Name**: `PortfolioCdkStack`
- **Region**: `us-east-1`
- **Removal Policy**: `DESTROY` (intended for non-production use)
- **S3 Auto-Delete Objects**: Enabled (cleans up S3 contents on stack removal)

## Deployment

Deployment is automated through GitHub Actions. To enable CI/CD, configure the following secrets in your repository:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

For manual deployment:

```bash
# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Deploy with AWS CDK
cdk bootstrap
cdk deploy

## Additional Notes

This stack is intended for personal or demo environments. For production use, adjust security settings, region configurations, and resource lifecycle policies accordingly.

GitHub Actions workflow file is located in .github/workflows/.
