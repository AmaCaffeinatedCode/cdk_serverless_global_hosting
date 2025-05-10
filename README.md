# Portfolio Infrastructure (AWS CDK)

This repository contains the infrastructure-as-code (IaC) configuration for deploying a static portfolio website on AWS, utilizing the AWS Cloud Development Kit (CDK) in Python.

## Overview

This CDK application provisions the following AWS resources:

- **Amazon S3 Bucket** – Configured for static website hosting with restricted public access.
- **Amazon CloudFront Distribution** – Enables HTTPS, global content delivery, and automatic redirects to HTTPS for fast and secure content delivery.
- **CloudFront Origin Access Control (OAC)** – Provides secure access to the S3 bucket, ensuring only CloudFront can retrieve content.
- **Asset Deployment** – Automates the deployment of static assets to S3 and manages CloudFront cache invalidation.

This setup ensures fast, secure delivery of the portfolio website, leveraging AWS CloudFront for low-latency and high-availability content serving.

## Stack Configuration

- **Stack Name:** `PortfolioCdkStack`
- **Region:** `us-east-1`
- **Removal Policy:** `DESTROY` (automatically cleans up resources on stack deletion for non-production use)
- **S3 Auto-Delete Objects:** Enabled (removes all S3 objects when the stack is deleted to avoid orphaned data)

## Deployment

Deployment is automated via GitHub Actions. To enable CI/CD, configure the following secrets in your repository:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Manual Deployment

1. **Set up the Python environment:**
   ``` bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Deploy with AWS CDK:**
   ``` bash
   cdk bootstrap
   cdk deploy
   ```

## GitHub Actions

### CI/CD Workflow (`main.yml`)

This repository includes a GitHub Actions workflow file located at `.github/workflows/main.yml` that automates the deployment process.

To skip the CI/CD pipeline during specific commits, add the `[skip-ci]` label to your commit message. This prevents the pipeline from triggering for that specific commit.

**Note:** The `main` branch will always trigger the pipeline, regardless of conditions, as it is treated as the production environment.

### Stack Destruction Workflow (`destroy.yml`)

A separate GitHub Actions workflow file, `.github/workflows/destroy.yml`, is provided for easy stack destruction. This workflow deletes all resources provisioned by the CDK stack.

To trigger the stack destruction, manually run the `destroy.yml` workflow from the GitHub Actions interface.

## Additional Notes

- This stack is intended for personal or demo environments. For production use, consider adjusting the following:
  - **Security Settings:** Review IAM policies and CloudFront security configurations.
  - **Region Configurations:** Ensure your resources are deployed in the desired region.
  - **Resource Lifecycle Policies:** Fine-tune retention and removal policies to meet production requirements.
  - **CloudFront Considerations:** Review traffic patterns to ensure resources are appropriately scaled for production traffic.
