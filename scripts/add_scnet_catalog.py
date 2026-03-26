#!/usr/bin/env python3
"""添加 SCNet 到模型目录"""
from pymongo import MongoClient
from datetime import datetime
import os

m = MongoClient(os.getenv('MONGO_URI','mongodb://mongodb:27017'))['tradingagents']
now = datetime.utcnow()

models = [
    {"name": "Qwen3-235B-A22B-Thinking-2507", "display_name": "Qwen3-Thinking", "context_length": 32000, "input_price_per_1k": 0.0005, "output_price_per_1k": 0.005, "capabilities": ["chat","reasoning"]},
    {"name": "DeepSeek-V3.2", "display_name": "DeepSeek-V3.2", "context_length": 128000, "input_price_per_1k": 0.0005, "output_price_per_1k": 0.00075, "capabilities": ["chat"]},
    {"name": "MiniMax-M2.5", "display_name": "MiniMax-M2.5", "context_length": 128000, "input_price_per_1k": 0.0005, "output_price_per_1k": 0.002, "capabilities": ["chat"]},
    {"name": "DeepSeek-R1-0528", "display_name": "DeepSeek-R1", "context_length": 128000, "input_price_per_1k": 0.001, "output_price_per_1k": 0.004, "capabilities": ["reasoning"]},
    {"name": "QwQ-32B", "display_name": "QwQ-32B", "context_length": 32000, "input_price_per_1k": 0.001, "output_price_per_1k": 0.004, "capabilities": ["reasoning"]},
    {"name": "DeepSeek-R1-Distill-Qwen-7B", "display_name": "DS-R1-Qwen-7B", "context_length": 32000, "input_price_per_1k": 0.0001, "output_price_per_1k": 0.0001, "capabilities": ["reasoning"]},
]

for item in models:
    item["currency"] = "CNY"
    item["description"] = ""

catalog = {"provider": "scnet", "provider_name": "SCNet算力中心", "models": models, "created_at": now, "updated_at": now}
m.model_catalog.delete_many({"provider": "scnet"})
m.model_catalog.insert_one(catalog)
print(f"OK: SCNet model_catalog created with {len(models)} models")
