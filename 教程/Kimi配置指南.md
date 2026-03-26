# 🌙 Kimi（月之暗面）配置指南

## 一、厂家管理配置

在前端「系统管理 → 大模型厂家管理」中添加：

| 字段 | 填写内容 |
|------|---------|
| **厂家ID** | `moonshot` |
| **显示名称** | `月之暗面 (Kimi)` |
| **描述** | 月之暗面 Kimi AI 大模型，支持超长上下文（最高 128K），支持视觉识别，中文优化，适合文档分析、图表解读和深度推理 |
| **官网** | `https://moonshot.cn` |
| **API文档** | `https://platform.moonshot.cn/docs` |
| **默认API地址** | `https://api.moonshot.cn/v1` |

---

## 二、环境变量配置

在 `.env` 文件中添加：

```bash
# 🌙 月之暗面 (Kimi) API 配置
# 获取地址: https://platform.moonshot.cn/
MOONSHOT_API_KEY=sk-your-moonshot-api-key-here
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_ENABLED=true
```

---

## 三、可用模型列表

| 模型ID | 上下文 | 能力等级 | 特性 | 推荐用途 |
|--------|--------|---------|------|---------|
| `moonshot-v1-8k` | 8K | 标准 (2) | 快速、经济 | 快速分析、日常任务 |
| `moonshot-v1-32k` | 32K | 高级 (3) | 长上下文 | 中等文档、标准分析 |
| `moonshot-v1-128k` | 128K | 专业 (4) | 超长上下文 | 长文档、财报分析 |
| `kimi-k2.5` | 变长 | 专业 (4) | 视觉识别 | 图表分析、图片识别 |

---

## 四、模型配置（前端添加）

### 4.1 Kimi 8K（快速分析）

| 字段 | 值 |
|------|-----|
| 模型ID | `moonshot-v1-8k` |
| 显示名称 | `Kimi 8K` |
| 能力等级 | `2` (标准) |
| 适用角色 | `quick_analysis` (快速分析) |
| 特性标签 | `tool_calling, fast_response, cost_effective` |
| 推荐分析深度 | `快速, 基础` |

### 4.2 Kimi 32K（标准分析）

| 字段 | 值 |
|------|-----|
| 模型ID | `moonshot-v1-32k` |
| 显示名称 | `Kimi 32K` |
| 能力等级 | `3` (高级) |
| 适用角色 | `both` (双重角色) |
| 特性标签 | `tool_calling, long_context` |
| 推荐分析深度 | `基础, 标准, 深度` |

### 4.3 Kimi 128K（深度分析）

| 字段 | 值 |
|------|-----|
| 模型ID | `moonshot-v1-128k` |
| 显示名称 | `Kimi 128K` |
| 能力等级 | `4` (专业) |
| 适用角色 | `deep_analysis` (深度分析) |
| 特性标签 | `tool_calling, long_context, reasoning` |
| 推荐分析深度 | `深度, 全面` |

### 4.4 Kimi K2.5（最新版，支持视觉）

| 字段 | 值 |
|------|-----|
| 模型ID | `kimi-k2.5` |
| 显示名称 | `Kimi K2.5` |
| 能力等级 | `4` (专业) |
| 适用角色 | `deep_analysis` (深度分析) |
| 特性标签 | `tool_calling, long_context, vision` |
| 推荐分析深度 | `深度, 全面` |

---

## 五、API 调用示例

### 5.1 基础文本对话

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

completion = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[
        {"role": "system", "content": "你是 Kimi，由月之暗面开发的AI助手。"},
        {"role": "user", "content": "你好，请介绍一下你自己。"},
    ],
)

print(completion.choices[0].message.content)
```

### 5.2 图像识别（Kimi K2.5）

```python
import os
import base64
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

# 读取并编码图片
image_path = "chart.png"
with open(image_path, "rb") as f:
    image_data = f.read()
image_url = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"

# 发送请求
completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {"role": "system", "content": "你是 Kimi。"},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
                {
                    "type": "text",
                    "text": "请分析这张K线图的趋势。",
                },
            ],
        },
    ],
)

print(completion.choices[0].message.content)
```

---

## 六、获取 API Key

1. 访问平台：https://platform.moonshot.cn/
2. 注册/登录账号
3. 进入「API 密钥管理」
4. 点击「创建新的 API Key」

---

## 七、测试连接

```bash
# 测试 Kimi API
cd /home/robot/agi/TradingAgents-CN/教程
python test_model_token.py --moonshot

# 或测试所有服务
python test_model_token.py
```

---

## 八、费用说明

| 模型 | 输入价格 | 输出价格 | 备注 |
|------|---------|---------|------|
| moonshot-v1-8k | ¥0.012/千tokens | ¥0.012/千tokens | 经济实惠 |
| moonshot-v1-32k | ¥0.024/千tokens | ¥0.024/千tokens | 平衡性价比 |
| moonshot-v1-128k | ¥0.06/千tokens | ¥0.06/千tokens | 长文档首选 |
| kimi-k2.5 | 按官网定价 | 按官网定价 | 最新模型 |

> 💡 新用户通常有免费额度，具体请查看官网。

---

## 九、使用建议

### 9.1 分析场景推荐

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 快速分析股票信息 | moonshot-v1-8k | 速度快、成本低 |
| 分析财报/研报 | moonshot-v1-128k | 支持超长文档 |
| 解读K线图表 | kimi-k2.5 | 支持视觉识别 |
| 日常多轮对话 | moonshot-v1-32k | 平衡性能和成本 |

### 9.2 与其他模型对比

| 特性 | Kimi | DeepSeek | 阿里百炼 |
|------|------|---------|---------|
| 最大上下文 | 128K | 64K | 32K |
| 视觉识别 | ✅ (K2.5) | ❌ | ✅ |
| 工具调用 | ✅ | ✅ | ✅ |
| 中文优化 | ✅ | ✅ | ✅ |
| 性价比 | 高 | 最高 | 中 |

---

## 十、常见问题

### Q1: 如何选择合适的模型？

- **日常分析**：`moonshot-v1-8k` 或 `moonshot-v1-32k`
- **长文档分析**：`moonshot-v1-128k`
- **图表识别**：`kimi-k2.5`

### Q2: 为什么返回 401 错误？

检查 API Key 是否正确配置，确保格式为 `sk-xxx`。

### Q3: 如何处理超长文档？

使用 `moonshot-v1-128k` 模型，最多支持 128K tokens（约 10 万汉字）。

### Q4: 支持流式输出吗？

支持，设置 `stream=True` 即可。

---

## 十一、技术架构说明

Kimi API 完全兼容 OpenAI 格式，系统通过 OpenAI 兼容适配器支持：

```
tradingagents/llm_adapters/
├── openai_compatible_base.py  # 基类（Kimi 使用此适配器）
└── deepseek_adapter.py        # DeepSeek 适配器示例
```

**配置流程**：
1. 添加环境变量 `MOONSHOT_API_KEY`
2. 在前端添加厂家配置
3. 添加模型配置
4. 系统自动识别并通过 OpenAI 兼容适配器调用
