from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct

class PortfolioCdkApp(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id,
            stack_name="PortfolioCdkStack",
            description="Portfolio website infrastructure stack",
            tags={"project": "portfolio"},
            env={"region": "us-east-1"},
            **kwargs
        )

        # Private S3 bucket
        website_bucket = s3.Bucket(self, "WebsiteBucket",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # CloudFront Origin Access Control (OAC)
        oac = cloudfront.CfnOriginAccessControl(self, "OAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="PortfolioOAC",
                description="OAC for S3 bucket access via CloudFront",
                signing_behavior="always",
                signing_protocol="sigv4",
                origin_type="s3"
            )
        )

        # CloudFront Distribution with OAC
        distribution = cloudfront.CfnDistribution(self, "WebsiteDistribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                enabled=True,
                default_root_object="index.html",
                origins=[
                    cloudfront.CfnDistribution.OriginProperty(
                        id="S3Origin",
                        domain_name=website_bucket.bucket_website_domain_name,
                        origin_access_control_id=oac.ref,
                        s3_origin_config=cloudfront.CfnDistribution.S3OriginConfigProperty(
                            origin_access_identity=""
                        )
                    )
                ],
                default_cache_behavior=cloudfront.CfnDistribution.DefaultCacheBehaviorProperty(
                    target_origin_id="S3Origin",
                    viewer_protocol_policy="redirect-to-https",
                    allowed_methods=["GET", "HEAD"],
                    cached_methods=["GET", "HEAD"],
                    compress=True,
                    cache_policy_id="658327ea-f89d-4fab-a63d-7e88639e58f6"  # AWS managed: CachingOptimized
                )
            )
        )

        # Grant bucket access to CloudFront service principal
        website_bucket.add_to_resource_policy(
            s3.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{website_bucket.bucket_arn}/*"],
                principals=[s3.ArnPrincipal("arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity E*")],
                conditions={"StringEquals": {"AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.ref}"}}
            )
        )

        # Upload website files to S3
        s3deploy.BucketDeployment(self, "WebsiteDeployment",
            sources=[s3deploy.Source.asset("./website")],
            destination_bucket=website_bucket,
            distribution=cloudfront.Distribution.from_distribution_attributes(
                self, "DistAttr",
                distribution_id=distribution.ref,
                domain_name=cloudfront.Fn.get_att(distribution.logical_id, "DomainName").to_string()
            ),
            distribution_paths=["/*"]
        )

        # Output CloudFront domain
        CfnOutput(self, "WebsiteURL", value=cloudfront.Fn.get_att(distribution.logical_id, "DomainName").to_string())
