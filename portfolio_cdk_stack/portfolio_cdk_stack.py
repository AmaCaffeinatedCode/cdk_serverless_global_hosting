from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct

class PortfolioCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id,
            stack_name="PortfolioCdkStack",
            description="Portfolio website infrastructure stack",
            tags={"Project": "Portfolio"},
            env={"region": "us-east-1"},
            **kwargs
        )

        # S3 public access configuration explicitly allowing public read
        allow_public_access = s3.BlockPublicAccess(
            block_public_acls=False,
            ignore_public_acls=False,
            block_public_policy=False,
            restrict_public_buckets=False,
        )

        # S3 bucket for static website hosting
        website_bucket = s3.Bucket(self, "WebsiteBucket",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=True,
            block_public_access=allow_public_access,
            removal_policy=RemovalPolicy.DESTROY,         # Destroy bucket on stack deletion (for dev/portfolio use)
            auto_delete_objects=True                      # Automatically delete objects when destroying stack
        )

        # CloudFront distribution to serve the S3 bucket content securely
        distribution = cloudfront.Distribution(self, "WebsiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3StaticWebsiteOrigin(website_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            )
        )

        # Deploy static assets from the local ./website directory to the S3 bucket
        s3deploy.BucketDeployment(self, "WebsiteDeployment",
            sources=[s3deploy.Source.asset("./website")],  # Local path to static site files
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=["/*"]                      # Invalidate all paths after upload
        )

        # Output the CloudFront distribution domain name
        CfnOutput(self, "WebsiteURL", value=distribution.distribution_domain_name)
