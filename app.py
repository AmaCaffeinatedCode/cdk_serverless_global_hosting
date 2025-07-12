#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_cdk import Tags
from portfolio_cdk_app.portfolio_cdk_app import PortfolioCdkApp

RESOURCE_TAGS = {
    "project_url": os.getenv("PROJECT_URL"),
    "Environment": os.getenv("ENVIRONMENT", "dev")
}

app = cdk.App()

for key, value in RESOURCE_TAGS.items():
    if value:
        Tags.of(app).add(key, value)

PortfolioCdkApp(app, "PortfolioCdkApp")

app.synth()
