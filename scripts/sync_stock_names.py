"""同步股票名称到 MongoDB"""
from pymongo import MongoClient
from datetime import datetime

MONGO_URL = 'mongodb://admin:tradingagents123@mongodb:27017/tradingagents?authSource=admin'
client = MongoClient(MONGO_URL)
db = client['tradingagents']

# 股票基础信息（已修正错误数据）
# 注意：此脚本仅用于手动同步，正式数据应从数据源自动获取
stocks = [
    # A股
    {'code': '000516', 'name': '陕国投A', 'source': 'manual', 'market': 'A股'},
    {'code': '000725', 'name': '京东方A', 'source': 'manual', 'market': 'A股'},
    {'code': '002385', 'name': '大北农', 'source': 'manual', 'market': 'A股'},
    {'code': '002916', 'name': '深南电路', 'source': 'manual', 'market': 'A股'},
    {'code': '600009', 'name': '上海机场', 'source': 'manual', 'market': 'A股'},
    {'code': '600905', 'name': '三峡能源', 'source': 'manual', 'market': 'A股'},
    {'code': '601628', 'name': '中国人寿', 'source': 'manual', 'market': 'A股'},  # 修正：中国人寿是601628
    {'code': '601828', 'name': '交通银行', 'source': 'manual', 'market': 'A股'},  # 修正：交通银行是601828
    # 港股（不补0，直接使用用户输入格式）
    {'code': '1810', 'name': '小米集团-W', 'source': 'manual', 'market': '港股'},
    {'code': '2171', 'name': '科德教育', 'source': 'manual', 'market': '港股'},
    {'code': '2202', 'name': '万科企业', 'source': 'manual', 'market': '港股'},
    {'code': '3690', 'name': '美团-W', 'source': 'manual', 'market': '港股'},
    {'code': '9660', 'name': '农夫山泉', 'source': 'manual', 'market': '港股'},
    {'code': '9988', 'name': '阿里巴巴-SW', 'source': 'manual', 'market': '港股'},
]

for s in stocks:
    db.stock_basic_info.update_one(
        {'code': s['code']},
        {'$set': {**s, 'updated_at': datetime.utcnow()}},
        upsert=True
    )

print(f'Inserted {len(stocks)} stocks')

# 验证
total = db.stock_basic_info.count_documents({})
print(f'Total in stock_basic_info: {total}')
