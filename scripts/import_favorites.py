"""导入自选股到 MongoDB"""
from pymongo import MongoClient
from datetime import datetime

MONGO_URL = 'mongodb://admin:tradingagents123@mongodb:27017/tradingagents?authSource=admin'
client = MongoClient(MONGO_URL)
db = client['tradingagents']

# 自选股列表（已修正错误数据）
stocks = [
    {'stock_code': '000725', 'stock_name': '京东方A', 'market': 'A股'},
    {'stock_code': '002385', 'stock_name': '大北农', 'market': 'A股'},
    {'stock_code': '002916', 'stock_name': '深南电路', 'market': 'A股'},
    {'stock_code': '600009', 'stock_name': '上海机场', 'market': 'A股'},
    {'stock_code': '600905', 'stock_name': '三峡能源', 'market': 'A股'},
    {'stock_code': '601328', 'stock_name': '交通银行', 'market': 'A股'},  # 交通银行
    {'stock_code': '601628', 'stock_name': '中国人寿', 'market': 'A股'},  # 中国人寿
    {'stock_code': '601828', 'stock_name': '美凯龙', 'market': 'A股'},    # 美凯龙
    {'stock_code': '1810', 'stock_name': '小米集团-W', 'market': '港股'},
    {'stock_code': '2202', 'stock_name': '万科企业', 'market': '港股'},
    {'stock_code': '3690', 'stock_name': '美团-W', 'market': '港股'},
    {'stock_code': '9660', 'stock_name': '农夫山泉', 'market': '港股'},
    {'stock_code': '9988', 'stock_name': '阿里巴巴-SW', 'market': '港股'},
]

# admin 用户的 ID (字符串形式)
user_id = '69c53e8a84ccd93eaaf997ce'

# 构建自选股数据
favorites = []
for s in stocks:
    favorites.append({
        'stock_code': s['stock_code'],
        'stock_name': s['stock_name'],
        'market': s['market'],
        'added_at': datetime.utcnow(),
        'tags': [],
        'notes': '',
        'alert_price_high': None,
        'alert_price_low': None
    })

# 插入到 user_favorites 集合
result = db.user_favorites.update_one(
    {'user_id': user_id},
    {
        '$setOnInsert': {'user_id': user_id, 'created_at': datetime.utcnow()},
        '$set': {'favorites': favorites, 'updated_at': datetime.utcnow()}
    },
    upsert=True
)

print(f'Upserted: {result.upserted_id}')
print(f'Matched: {result.matched_count}')
print(f'Modified: {result.modified_count}')
print(f'Added {len(favorites)} stocks to favorites for user {user_id}')
