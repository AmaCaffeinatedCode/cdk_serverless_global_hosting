# AWS CDK Serverless Website Hosting Infrastructure

This repository provides an infrastructure-as-code (IaC) setup to deploy a fully serverless static website on AWS. Using AWS CDK with Python, it automates provisioning of all necessary AWS services such as S3, CloudFront, Route 53, ACM, and WAF to deliver secure, scalable, and globally available web content with minimal operational overhead.

## Project Overview

This CDK application provisions the following AWS resources:

- **Amazon S3 Bucket** – Configured for static website hosting with restricted public access.
- **Amazon CloudFront Distribution** – Enables HTTPS, global content delivery, and automatic redirects to HTTPS for fast and secure content delivery.
- **CloudFront Origin Access Control (OAC)** – Provides secure access to the S3 bucket, ensuring only CloudFront can retrieve content.
- **Amazon Route 53 Hosted Zone** – Automatically creates a public hosted zone for the domain and manages DNS records.
- **AWS Certificate Manager (ACM)** – Provisions an SSL/TLS certificate for HTTPS using the custom domain.
- **AWS WAF (Web Application Firewall)** – Adds a Web ACL using AWS-managed rules to protect against common web threats like SQL injection and cross-site scripting (XSS).
- **Route 53 Alias Record** – Connects the custom domain and subdomain to the CloudFront distribution.
- **HTTP to HTTPS Redirects** – Automatically redirects HTTP traffic to HTTPS for secure communication.
- **Asset Deployment** – Automates the deployment of static assets to S3 and manages CloudFront cache invalidation.

This setup ensures fast, secure delivery of the website, leveraging AWS CloudFront and Route 53 for low-latency, high-availability content serving, with enhanced security via AWS WAF.

## Stack Configuration

- **Stack Name:** `CdkServerlessGlobalHostingStack`
- **Region:** `us-east-1`
- **Removal Policy:** `DESTROY` (automatically cleans up resources on stack deletion for non-production use)
- **S3 Auto-Delete Objects:** Enabled (removes all S3 objects when the stack is destroyed to avoid orphaned data)
- **Domain Configuration:** Uses dynamic values from environment variables (`ROOT_DOMAIN` and `SUBDOMAIN`)
- **WAF Rules:** Uses `AWSManagedRulesCommonRuleSet` for protection against common web exploits such as SQL injection, cross-site scripting (XSS), and known bad inputs.

## Usage

Deployment is automated via GitHub Actions. To enable CI/CD, configure the following **repository secrets**:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PRIVATE_REPO_TOKEN` – GitHub token with repo scope
- `PRIVATE_REPO_OWNER` – GitHub username or organization that owns the private repo (e.g. `Example_User`)
- `PRIVATE_REPO_NAME` – Name of the private repo (e.g. `Website_repo`)
- `ROOT_DOMAIN` – Your domain name (e.g. `example.com`)
- `SUBDOMAIN` – Subdomain for the website (default: `www`)

These values will be injected into the GitHub Actions workflow as environment variables and used by CDK at deploy time.

### Manual Deployment

Before deploying, ensure you have a `website` folder inside the project root. This folder should contain your static website assets (HTML, CSS, JS, images, etc.) that will be deployed to the S3 bucket.

``` bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables locally:

``` bash
export ROOT_DOMAIN=example.com
export SUBDOMAIN=www
export ENVIRONMENT=dev
export PROJECT_URL=https://github.com/<your-username>/<your-repo>
```

Deploy with AWS CDK:

``` bash
cdk bootstrap
cdk deploy
```

## GitHub Actions

### CI/CD Workflow (`deploy.yml`)

This repository includes a GitHub Actions workflow file located at `.github/workflows/deploy.yml` that automates the deployment process.

To skip the CI/CD pipeline during specific commits, add the `[skip-ci]` label to your commit message. This prevents the pipeline from triggering for that specific commit.

**Note:** The `main` branch will always trigger the pipeline, regardless of conditions, as it is treated as the production environment.

Environment-specific values like domain configuration (`ROOT_DOMAIN`, `SUBDOMAIN`) are injected securely via GitHub Secrets.

### Stack Destruction Workflow (`destroy.yml`)

A separate GitHub Actions workflow file, `.github/workflows/destroy.yml`, is provided for easy stack destruction. This workflow deletes all resources provisioned by the CDK stack.

To trigger the stack destruction, manually run the `destroy.yml` workflow from the GitHub Actions interface.

## Additional Notes

- This stack is intended for personal or demo environments. For production use, consider adjusting the following:
  - **Security Settings:** Review IAM policies, WAF rules, and CloudFront security configurations.
  - **Region Configurations:** Ensure your resources are deployed in the desired region.
  - **Domain Validation:** ACM certificates require domain validation through DNS. Ensure your hosted zone setup supports this.
  - **WAF Rules:** Expand WAF protections by adding managed rules, rate limits, or geo-blocking as needed.
  - **CloudFront Considerations:** Review traffic patterns and cost expectations to ensure optimal performance under production loads.
  - **DNS TTL:** Adjust TTL values for Route 53 records based on caching needs.
