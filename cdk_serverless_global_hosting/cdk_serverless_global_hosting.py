from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_wafv2 as wafv2,
    Fn
)
from constructs import Construct
import os


class CdkServerlessGlobalHostingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id,
            stack_name="CdkServerlessGlobalHostingStack",
            description="Serverless global hosting infrastructure stack",
            tags={"project": "cdk_serverless_global_hosting"},
            env={"region": "us-east-1"},
            **kwargs
        )

        # --- Dynamic domain configuration ---
        root_domain = os.getenv("ROOT_DOMAIN", "example.com")
        subdomain = os.getenv("SUBDOMAIN", "www")
        full_domain = f"{subdomain}.{root_domain}"

        # --- Create Hosted Zone ---
        hosted_zone = route53.PublicHostedZone(self, "HostedZone",
            zone_name=root_domain
        )

        # --- Create ACM certificate for the domain and subdomain ---
        certificate = acm.Certificate(self, "Certificate",
            domain_name=full_domain,
            subject_alternative_names=[root_domain],
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        # --- Create Web ACL with AWS Managed Rules ---
        web_acl = wafv2.CfnWebACL(self, "WebACL",
            scope="CLOUDFRONT",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="GlobalHostingWebACL",
                sampled_requests_enabled=True
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedCommonRuleSet",
                    priority=1,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesCommonRuleSet",
                            vendor_name="AWS"
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="CommonRuleSet",
                        sampled_requests_enabled=True
                    )
                )
            ]
        )
        
        # --- Create private S3 bucket for website content ---
        website_bucket = s3.Bucket(self, "WebsiteBucket",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # --- Create OAC for CloudFront to access S3 securely ---
        oac = cloudfront.CfnOriginAccessControl(self, "OAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="GlobalHostingOAC",
                description="OAC for S3 bucket access via CloudFront",
                signing_behavior="always",
                signing_protocol="sigv4",
                origin_access_control_origin_type="s3"
            )
        )

        # --- CloudFront Distribution with redirects, WAF, OAC, SSL, and custom errors ---
        distribution = cloudfront.CfnDistribution(self, "WebsiteDistribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                enabled=True,
                default_root_object="index.html",
                aliases=[full_domain, root_domain],
                viewer_certificate=cloudfront.CfnDistribution.ViewerCertificateProperty(
                    acm_certificate_arn=certificate.certificate_arn,
                    ssl_support_method="sni-only",
                    minimum_protocol_version="TLSv1.2_2021"
                ),
                web_acl_id=web_acl.attr_arn,
                origins=[
                    cloudfront.CfnDistribution.OriginProperty(
                        id="S3Origin",
                        domain_name=website_bucket.bucket_regional_domain_name,
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
                    cache_policy_id="658327ea-f89d-4fab-a63d-7e88639e58f6"  # AWS managed caching policy
                ),
                custom_error_responses=[
                    cloudfront.CfnDistribution.CustomErrorResponseProperty(
                        error_code=403,
                        response_code=404,
                        response_page_path="/error.html"
                    ),
                    cloudfront.CfnDistribution.CustomErrorResponseProperty(
                        error_code=404,
                        response_code=404,
                        response_page_path="/error.html"
                    )
                ]
            )
        )

        # --- Grant CloudFront permission to access S3 content ---
        website_bucket.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[f"{website_bucket.bucket_arn}/*"],
            principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
            conditions={
                "StringEquals": {
                    "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.ref}"
                }
            }
        ))

        # --- Deploy website files to S3 and invalidate CloudFront cache ---
        s3deploy.BucketDeployment(self, "WebsiteDeployment",
            sources=[s3deploy.Source.asset("./website", exclude=[".git", "README.md"])],
            destination_bucket=website_bucket,
            distribution=cloudfront.Distribution.from_distribution_attributes(
                self, "DistAttr",
                distribution_id=distribution.ref,
                domain_name=Fn.get_att(distribution.logical_id, "DomainName").to_string()
            ),
            distribution_paths=["/*"]
        )

        # --- Create A records (root and subdomain) pointing to CloudFront ---
        cloudfront_target = targets.CloudFrontTarget(
            cloudfront.Distribution.from_distribution_attributes(
                self, "ImportedDist",
                distribution_id=distribution.ref,
                domain_name=Fn.get_att(distribution.logical_id, "DomainName").to_string()
            )
        )

        route53.ARecord(self, "RootAliasRecord",
            zone=hosted_zone,
            record_name=root_domain,
            target=route53.RecordTarget.from_alias(cloudfront_target)
        )

        route53.ARecord(self, "WWWAliasRecord",
            zone=hosted_zone,
            record_name=subdomain,
            target=route53.RecordTarget.from_alias(cloudfront_target)
        )

        # --- Output distribution domain name ---
        CfnOutput(self, "WebsiteURL",
            value=Fn.get_att(distribution.logical_id, "DomainName").to_string()
        )
