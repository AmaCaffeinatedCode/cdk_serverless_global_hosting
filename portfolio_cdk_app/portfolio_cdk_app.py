from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    Fn  # Function to resolve CloudFormation intrinsic functions
)
from constructs import Construct


class PortfolioCdkApp(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id,
            stack_name="PortfolioCdkStack",
            description="Portfolio website infrastructure stack",
            tags={"project": "portfolio"},
            env={"region": "us-east-1"},  # Define the region for deployment
            **kwargs
        )

        # Private S3 bucket for hosting website content
        website_bucket = s3.Bucket(self, "WebsiteBucket",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=False,  # Restrict public access to bucket
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Block all public access
            removal_policy=RemovalPolicy.DESTROY,  # Destroy bucket on stack deletion
            auto_delete_objects=True  # Automatically delete objects when the bucket is deleted
        )

        # CloudFront Origin Access Control (OAC) for secure access to S3 bucket
        oac = cloudfront.CfnOriginAccessControl(self, "OAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="PortfolioOAC",
                description="OAC for S3 bucket access via CloudFront",
                signing_behavior="always",  # Sign requests for S3 access
                signing_protocol="sigv4",  # Use SigV4 for signing requests
                origin_access_control_origin_type="s3"  # Origin type is S3
            )
        )

        # CloudFront Distribution setup with OAC
        distribution = cloudfront.CfnDistribution(self, "WebsiteDistribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                enabled=True,  # Enable CloudFront distribution
                default_root_object="index.html",  # Set the default root object
                origins=[
                    cloudfront.CfnDistribution.OriginProperty(
                        id="S3Origin",
                        domain_name=website_bucket.bucket_regional_domain_name,
                        origin_access_control_id=oac.ref,  # Use OAC for secure access
                        s3_origin_config=cloudfront.CfnDistribution.S3OriginConfigProperty(
                            origin_access_identity=""  # Origin access identity is empty because OAC is used
                        )
                    )
                ],
                default_cache_behavior=cloudfront.CfnDistribution.DefaultCacheBehaviorProperty(
                    target_origin_id="S3Origin",  # Target the S3 origin for this cache behavior
                    viewer_protocol_policy="redirect-to-https",  # Enforce HTTPS for viewers
                    allowed_methods=["GET", "HEAD"],  # Only allow GET and HEAD methods
                    cached_methods=["GET", "HEAD"],  # Cache GET and HEAD methods
                    compress=True,  # Enable compression for faster delivery
                    cache_policy_id="658327ea-f89d-4fab-a63d-7e88639e58f6"  # Use AWS managed cache policy (CachingOptimized)
                )
            )
        )

        # Grant CloudFront access to the S3 bucket
        website_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{website_bucket.bucket_arn}/*"], # Access all objects in the bucket
                principals=[iam.ArnPrincipal(oac.ref)],  # CloudFront service principal
                conditions={"StringEquals": {"AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.ref}"}}
            )
        )

        # Deploy website files to S3 bucket
        s3deploy.BucketDeployment(self, "WebsiteDeployment",
            sources=[s3deploy.Source.asset("./website")],  # Local directory containing website files
            destination_bucket=website_bucket,
            distribution=cloudfront.Distribution.from_distribution_attributes(
                self, "DistAttr",
                distribution_id=distribution.ref,
                domain_name=Fn.get_att(distribution.logical_id, "DomainName").to_string()  # Get CloudFront domain name
            ),
            distribution_paths=["/*"]  # Deploy all files to CloudFront cache
        )

        # Output the CloudFront distribution domain name (website URL)
        CfnOutput(self, "WebsiteURL", value=Fn.get_att(distribution.logical_id, "DomainName").to_string())

