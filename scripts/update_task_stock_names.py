"""更新任务中的股票名称"""
from pymongo import MongoClient
from datetime import datetime

MONGO_URL = 'mongodb://admin:tradingagents123@mongodb:27017/tradingagents?authSource=admin'
client = MongoClient(MONGO_URL)
db = client['tradingagents']

# 股票名称映射（已修正错误数据）
stock_names = {
    '000516': '陕国投A',
    '000725': '京东方A',
    '002385': '大北农',
    '002916': '深南电路',
    '600009': '上海机场',
    '600905': '三峡能源',
    '601628': '中国人寿',  # 修正：中国人寿是601628
    '601828': '交通银行',  # 修正：交通银行是601828
    '1810': '小米集团-W',
    '2171': '科德教育',
    '2202': '万科企业',
    '3690': '美团-W',
    '9660': '农夫山泉',
    '9988': '阿里巴巴-SW',
}

# 更新 analysis_tasks
updated = 0
for code, name in stock_names.items():
    result = db.analysis_tasks.update_many(
        {'stock_code': code},
        {'$set': {'stock_name': name}}
    )
    updated += result.modified_count
    if result.modified_count > 0:
        print(f'Updated {result.modified_count} tasks for {code} -> {name}')

print(f'Total updated: {updated}')
