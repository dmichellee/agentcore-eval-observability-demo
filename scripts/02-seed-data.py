#!/usr/bin/env python3
"""
DynamoDB에 목업 데이터 적재 스크립트
Products 30개, Orders 15건, Customers 3명
"""
import os
import sys
import json
from decimal import Decimal

import boto3

# 프로젝트 루트의 backend/data 를 import path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from data.products import PRODUCTS
from data.orders import ORDERS
from data.customers import CUSTOMERS

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ENV = os.environ.get("ENV", "dev")
PREFIX = "vroom-dash"

PRODUCTS_TABLE = os.environ.get("PRODUCTS_TABLE", f"{PREFIX}-products-{ENV}")
ORDERS_TABLE = os.environ.get("ORDERS_TABLE", f"{PREFIX}-orders-{ENV}")
CUSTOMERS_TABLE = os.environ.get("CUSTOMERS_TABLE", f"{PREFIX}-customers-{ENV}")


def convert_floats(obj):
    """Python float/int → DynamoDB Decimal 변환 (재귀)"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, int):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_floats(i) for i in obj]
    return obj


def seed_table(table_name: str, items: list[dict], key_name: str):
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(table_name)

    print(f"  Seeding {table_name} ({len(items)} items)...")
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=convert_floats(item))
    print(f"  -> {table_name}: {len(items)} items loaded")


def main():
    print("==========================================")
    print(" DynamoDB 목업 데이터 적재")
    print(f" Region: {AWS_REGION}, Env: {ENV}")
    print("==========================================")

    seed_table(PRODUCTS_TABLE, PRODUCTS, "product_id")
    seed_table(ORDERS_TABLE, ORDERS, "order_id")
    seed_table(CUSTOMERS_TABLE, CUSTOMERS, "customer_id")

    print("")
    print("Data seeding completed!")
    print(f"  Products: {len(PRODUCTS)} items -> {PRODUCTS_TABLE}")
    print(f"  Orders:   {len(ORDERS)} items -> {ORDERS_TABLE}")
    print(f"  Customers:{len(CUSTOMERS)} items -> {CUSTOMERS_TABLE}")


if __name__ == "__main__":
    main()
