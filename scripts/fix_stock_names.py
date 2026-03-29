"""修复 MongoDB 中的错误股票名称

问题：
1. 601828 被错误标记为"中国人寿"，实际应该是"美凯龙"
2. 港股代码格式不一致（有补0和不补0的）

正确的代码对应关系（来源：东方财富网）：
- 601328 = 交通银行
- 601628 = 中国人寿
- 601828 = 美凯龙

解决方案：
1. 修正 601828 的名称为"美凯龙"
2. 统一港股代码格式（不补0）
"""
from pymongo import MongoClient
from datetime import datetime

MONGO_URL = 'mongodb://admin:tradingagents123@mongodb:27017/tradingagents?authSource=admin'
client = MongoClient(MONGO_URL)
db = client['tradingagents']

print("=" * 50)
print("修复 MongoDB 中的错误股票名称")
print("=" * 50)

# 1. 修正 stock_basic_info 中的错误数据
print("\n[1] 修正 stock_basic_info 集合...")

# 修正 601828 -> 美凯龙
result = db.stock_basic_info.update_many(
    {'code': '601828'},
    {'$set': {'name': '美凯龙', 'updated_at': datetime.utcnow()}}
)
print(f"  601828 -> 美凯龙: 修正了 {result.modified_count} 条记录")

# 确保 601628 是中国人寿
result = db.stock_basic_info.update_many(
    {'code': '601628'},
    {'$set': {'name': '中国人寿', 'updated_at': datetime.utcnow()}}
)
print(f"  601628 -> 中国人寿: 修正了 {result.modified_count} 条记录")

# 确保 601328 是交通银行
result = db.stock_basic_info.update_many(
    {'code': '601328'},
    {'$set': {'name': '交通银行', 'updated_at': datetime.utcnow()}}
)
print(f"  601328 -> 交通银行: 修正了 {result.modified_count} 条记录")

# 2. 修正 analysis_tasks 中的错误数据
print("\n[2] 修正 analysis_tasks 集合...")

result = db.analysis_tasks.update_many(
    {'stock_code': '601828'},
    {'$set': {'stock_name': '美凯龙'}}
)
print(f"  601828 -> 美凯龙: 修正了 {result.modified_count} 条任务记录")

result = db.analysis_tasks.update_many(
    {'stock_code': '601628'},
    {'$set': {'stock_name': '中国人寿'}}
)
print(f"  601628 -> 中国人寿: 修正了 {result.modified_count} 条任务记录")

result = db.analysis_tasks.update_many(
    {'stock_code': '601328'},
    {'$set': {'stock_name': '交通银行'}}
)
print(f"  601328 -> 交通银行: 修正了 {result.modified_count} 条任务记录")

# 3. 修正 user_favorites 中的错误数据
print("\n[3] 修正 user_favorites 集合...")

# 查找所有包含错误数据的用户
for stock_code, correct_name in [('601828', '美凯龙'), ('601628', '中国人寿'), ('601328', '交通银行')]:
    users = db.user_favorites.find({'favorites.stock_code': stock_code})
    for user in users:
        user_id = user.get('user_id')
        favorites = user.get('favorites', [])
        updated = False
        for fav in favorites:
            if fav.get('stock_code') == stock_code:
                fav['stock_name'] = correct_name
                updated = True
        if updated:
            db.user_favorites.update_one(
                {'user_id': user_id},
                {'$set': {'favorites': favorites, 'updated_at': datetime.utcnow()}}
            )
            print(f"  修正用户 {user_id} 的 {stock_code} -> {correct_name}")

# 4. 验证修正结果
print("\n[4] 验证修正结果...")

for code, expected_name in [('601828', '美凯龙'), ('601628', '中国人寿'), ('601328', '交通银行')]:
    info = db.stock_basic_info.find_one({'code': code})
    if info:
        actual_name = info.get('name')
        status = "✅" if actual_name == expected_name else "❌"
        print(f"  {code} 当前名称: {actual_name} (应为: {expected_name}) {status}")
    else:
        print(f"  {code} 在 stock_basic_info 中不存在")

print("\n" + "=" * 50)
print("修复完成！")
print("=" * 50)
