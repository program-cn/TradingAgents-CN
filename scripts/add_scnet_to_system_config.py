#!/usr/bin/env python3
"""添加 SCNet 配置到 system_configs.llm_configs"""
from pymongo import MongoClient
from datetime import datetime
import os

m = MongoClient(os.getenv('MONGO_URI','mongodb://mongodb:27017'))['tradingagents']

scnet_configs = [
    {
        "provider": "scnet",
        "model_name": "Qwen3-235B-A22B-Thinking-2507",
        "model_display_name": "Qwen3-Thinking - 推理增强",
        "api_key": "",
        "api_base": "",
        "max_tokens": 8000,
        "temperature": 0.7,
        "timeout": 60,
        "retry_times": 3,
        "enabled": True,
        "description": "通义千问3推理增强版",
        "model_category": "reasoning",
        "custom_endpoint": None,
        "enable_memory": True,
        "enable_debug": True,
        "priority": 1,
        "input_price_per_1k": 0.0005,
        "output_price_per_1k": 0.005,
        "currency": "CNY",
        "capability_level": 5,
        "suitable_roles": ["both"],
        "features": ["reasoning", "thinking"],
        "recommended_depths": ["标准", "深度", "全面"],
        "performance_metrics": {"speed": 3, "cost": 3, "quality": 5}
    },
    {
        "provider": "scnet",
        "model_name": "DeepSeek-V3.2",
        "model_display_name": "DeepSeek-V3.2 - 通用对话",
        "api_key": "",
        "api_base": "",
        "max_tokens": 8000,
        "temperature": 0.7,
        "timeout": 60,
        "retry_times": 3,
        "enabled": True,
        "description": "DeepSeek最新版通用模型",
        "model_category": "chat",
        "custom_endpoint": None,
        "enable_memory": True,
        "enable_debug": True,
        "priority": 2,
        "input_price_per_1k": 0.0005,
        "output_price_per_1k": 0.00075,
        "currency": "CNY",
        "capability_level": 5,
        "suitable_roles": ["both"],
        "features": ["fast_response", "cost_effective"],
        "recommended_depths": ["标准", "深度"],
        "performance_metrics": {"speed": 4, "cost": 4, "quality": 4}
    },
    {
        "provider": "scnet",
        "model_name": "MiniMax-M2.5",
        "model_display_name": "MiniMax-M2.5 - 长上下文",
        "api_key": "",
        "api_base": "",
        "max_tokens": 8000,
        "temperature": 0.7,
        "timeout": 60,
        "retry_times": 3,
        "enabled": True,
        "description": "MiniMax大模型128K上下文",
        "model_category": "chat",
        "custom_endpoint": None,
        "enable_memory": True,
        "enable_debug": True,
        "priority": 3,
        "input_price_per_1k": 0.0005,
        "output_price_per_1k": 0.002,
        "currency": "CNY",
        "capability_level": 4,
        "suitable_roles": ["both"],
        "features": ["long_context"],
        "recommended_depths": ["标准", "深度"],
        "performance_metrics": {"speed": 3, "cost": 3, "quality": 4}
    },
    {
        "provider": "scnet",
        "model_name": "DeepSeek-R1-0528",
        "model_display_name": "DeepSeek-R1 - 推理模型",
        "api_key": "",
        "api_base": "",
        "max_tokens": 8000,
        "temperature": 0.7,
        "timeout": 60,
        "retry_times": 3,
        "enabled": True,
        "description": "DeepSeek推理增强版",
        "model_category": "reasoning",
        "custom_endpoint": None,
        "enable_memory": True,
        "enable_debug": True,
        "priority": 4,
        "input_price_per_1k": 0.001,
        "output_price_per_1k": 0.004,
        "currency": "CNY",
        "capability_level": 5,
        "suitable_roles": ["both"],
        "features": ["reasoning"],
        "recommended_depths": ["深度", "全面"],
        "performance_metrics": {"speed": 2, "cost": 3, "quality": 5}
    },
    {
        "provider": "scnet",
        "model_name": "QwQ-32B",
        "model_display_name": "QwQ-32B - 推理模型",
        "api_key": "",
        "api_base": "",
        "max_tokens": 8000,
        "temperature": 0.7,
        "timeout": 60,
        "retry_times": 3,
        "enabled": True,
        "description": "通义千问推理模型",
        "model_category": "reasoning",
        "custom_endpoint": None,
        "enable_memory": True,
        "enable_debug": True,
        "priority": 5,
        "input_price_per_1k": 0.001,
        "output_price_per_1k": 0.004,
        "currency": "CNY",
        "capability_level": 4,
        "suitable_roles": ["both"],
        "features": ["reasoning"],
        "recommended_depths": ["标准", "深度"],
        "performance_metrics": {"speed": 3, "cost": 3, "quality": 4}
    },
    {
        "provider": "scnet",
        "model_name": "DeepSeek-R1-Distill-Qwen-7B",
        "model_display_name": "DS-R1-Qwen-7B - 轻量推理",
        "api_key": "",
        "api_base": "",
        "max_tokens": 8000,
        "temperature": 0.7,
        "timeout": 60,
        "retry_times": 3,
        "enabled": True,
        "description": "性价比最高的推理模型",
        "model_category": "reasoning",
        "custom_endpoint": None,
        "enable_memory": True,
        "enable_debug": True,
        "priority": 6,
        "input_price_per_1k": 0.0001,
        "output_price_per_1k": 0.0001,
        "currency": "CNY",
        "capability_level": 3,
        "suitable_roles": ["both"],
        "features": ["cost_effective", "reasoning"],
        "recommended_depths": ["标准"],
        "performance_metrics": {"speed": 5, "cost": 5, "quality": 3}
    }
]

# 获取当前配置
sys_config = m.system_configs.find_one()
if sys_config:
    llm_configs = sys_config.get('llm_configs', [])
    # 移除已有的 scnet 配置
    llm_configs = [c for c in llm_configs if c.get('provider') != 'scnet']
    # 添加新配置
    llm_configs.extend(scnet_configs)
    # 更新
    m.system_configs.update_one(
        {'_id': sys_config['_id']},
        {'$set': {'llm_configs': llm_configs, 'updated_at': datetime.utcnow()}}
    )
    print(f'OK: Added {len(scnet_configs)} SCNet configs. Total: {len(llm_configs)}')
else:
    print('ERROR: No system_configs found')
