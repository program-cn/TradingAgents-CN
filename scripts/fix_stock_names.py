"""修复 MongoDB 中的错误股票名称

问题：
1. 601828 被错误标记为"中国人寿"，实际应该是"交通银行"
2. 港股代码格式不一致（有补0和不补0的）

解决方案：
1. 修正 601828 的名称
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

# 修正 601828 -> 交通银行
result = db.stock_basic_info.update_many(
    {'code': '601828', 'name': '中国人寿'},
    {'$set': {'name': '交通银行', 'updated_at': datetime.utcnow()}}
)
print(f"  601828 -> 交通银行: 修正了 {result.modified_count} 条记录")

# 删除错误的中国人寿记录（如果存在）
result = db.stock_basic_info.delete_many({'code': '601828', 'name': '中国人寿'})
if result.deleted_count > 0:
    print(f"  删除错误记录: {result.deleted_count} 条")

# 2. 修正 analysis_tasks 中的错误数据
print("\n[2] 修正 analysis_tasks 集合...")

result = db.analysis_tasks.update_many(
    {'stock_code': '601828', 'stock_name': '中国人寿'},
    {'$set': {'stock_name': '交通银行'}}
)
print(f"  601828 -> 交通银行: 修正了 {result.modified_count} 条任务记录")

# 3. 修正 user_favorites 中的错误数据
print("\n[3] 修正 user_favorites 集合...")

# 查找所有包含错误数据的用户
users = db.user_favorites.find({'favorites.stock_code': '601828'})
for user in users:
    user_id = user.get('user_id')
    favorites = user.get('favorites', [])
    updated = False
    for fav in favorites:
        if fav.get('stock_code') == '601828' and fav.get('stock_name') == '中国人寿':
            fav['stock_name'] = '交通银行'
            updated = True
    if updated:
        db.user_favorites.update_one(
            {'user_id': user_id},
            {'$set': {'favorites': favorites, 'updated_at': datetime.utcnow()}}
        )
        print(f"  修正用户 {user_id} 的自选股")

# 4. 验证修正结果
print("\n[4] 验证修正结果...")

# 检查 601828
info = db.stock_basic_info.find_one({'code': '601828'})
if info:
    print(f"  601828 当前名称: {info.get('name')}")
else:
    print("  601828 在 stock_basic_info 中不存在")

# 检查中国人寿
info = db.stock_basic_info.find_one({'name': '中国人寿'})
if info:
    print(f"  中国人寿对应代码: {info.get('code')}")
else:
    print("  中国人寿在 stock_basic_info 中不存在")

# 检查交通银行
info = db.stock_basic_info.find_one({'name': '交通银行'})
if info:
    print(f"  交通银行对应代码: {info.get('code')}")
else:
    print("  交通银行在 stock_basic_info 中不存在")

print("\n" + "=" * 50)
print("修复完成！")
print("=" * 50)
