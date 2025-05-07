#!/usr/bin/env python3
import os
import aws_cdk as cdk
from portfolio_cdk_app.portfolio_cdk_app import PortfolioCdkApp


app = cdk.App()
PortfolioCdkApp(app, "PortfolioCdkApp")
app.synth()
