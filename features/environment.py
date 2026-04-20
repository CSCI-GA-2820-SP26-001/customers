"""
BDD Environment Setup for Customer Service
"""
import os
import requests


def before_all(context):
    context.BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
    context.headers = {"Content-Type": "application/json"}
    context.resp = None


def before_scenario(context, scenario):
    context.created_customer_ids = []


def after_scenario(context, scenario):
    for customer_id in getattr(context, "created_customer_ids", []):
        requests.delete(f"{context.BASE_URL}/customers/{customer_id}", timeout=10)
