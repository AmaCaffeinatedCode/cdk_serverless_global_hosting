#!/usr/bin/env python3
import os
import aws_cdk as cdk
from portfolio_cdk_stack.portfolio_cdk_stack import PortfolioCdkStack


app = cdk.App()
PortfolioCdkStack(app, "PortfolioCdkStackStack")
app.synth()
