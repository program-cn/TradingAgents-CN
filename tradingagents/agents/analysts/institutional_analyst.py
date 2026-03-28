"""
机构分析师 - 分析北向资金、基金重仓、龙虎榜等机构行为
A股特色分析模块
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, ToolMessage
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")

# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler

# 导入工具日志装饰器
from tradingagents.utils.tool_logging import log_analyst_module


def _get_company_name_for_institutional(ticker: str, market_info: dict) -> str:
    """
    为机构分析师获取公司名称
    
    Args:
        ticker: 股票代码
        market_info: 市场信息字典
        
    Returns:
        str: 公司名称
    """
    try:
        if market_info['is_china']:
            # 中国A股：使用统一接口获取股票信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)
            
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [机构分析师] 成功获取股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                return f"股票代码{ticker}"
        else:
            return f"股票{ticker}"
            
    except Exception as e:
        logger.error(f"❌ [机构分析师] 获取公司名称失败: {e}")
        return f"股票{ticker}"


@log_analyst_module("institutional")
def create_institutional_analyst(llm, toolkit):
    """
    创建机构分析师
    
    专门分析A股市场中的机构行为，包括：
    - 北向资金流向和持股变化
    - 公募基金持仓变化
    - 龙虎榜游资动向
    - 机构整体态度判断
    """
    
    def institutional_analyst_node(state):
        logger.info(f"🏦 [机构分析师] ===== 开始分析 =====")
        
        # 工具调用计数器
        messages = state.get("messages", [])
        tool_message_count = sum(1 for msg in messages if isinstance(msg, ToolMessage))
        
        tool_call_count = state.get("institutional_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        
        if tool_message_count > tool_call_count:
            tool_call_count = tool_message_count
            logger.info(f"🔧 [工具调用计数] 更新计数器: {tool_call_count}")
        
        logger.info(f"🔧 [工具调用计数] 当前: {tool_call_count}/{max_tool_calls}")
        
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # 获取股票市场信息
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)
        
        # 只分析中国A股
        if not market_info['is_china']:
            logger.info(f"🏦 [机构分析师] 跳过非A股股票: {ticker}")
            return {
                "messages": [],
                "institutional_report": f"## 机构分析\n\n股票 {ticker} 为{market_info['market_name']}，暂不支持机构行为分析（此功能仅限A股）。",
                "sender": "InstitutionalAnalyst",
            }
        
        # 获取公司名称
        company_name = _get_company_name_for_institutional(ticker, market_info)
        logger.info(f"🏦 [机构分析师] 公司名称: {company_name}")
        
        # 导入机构分析工具
        from tradingagents.tools.institutional_analysis_tool import (
            get_north_money_flow,
            get_stock_north_holding,
            get_stock_fund_holding,
            get_stock_lhb_analysis,
            get_industry_comparison,
        )
        
        # 绑定工具
        tools = [
            get_north_money_flow,
            get_stock_north_holding,
            get_stock_fund_holding,
            get_stock_lhb_analysis,
            get_industry_comparison,
        ]
        
        logger.info(f"🏦 [机构分析师] 绑定工具: {[t.name for t in tools]}")
        
        # 系统提示词
        system_message = f"""你是一位专业的A股机构行为分析师，专注于分析北向资金、公募基金、游资等机构投资者的行为。

**分析对象**：
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_info['market_name']}
- 分析日期：{current_date}

**你的分析维度**：

1. **北向资金分析**（重点关注）
   - 整体北向资金流向趋势
   - 该股票北向资金持股比例和变化
   - 外资态度判断

2. **基金持股分析**
   - 公募基金持仓数量和变化
   - 主要持仓基金动向
   - 机构认可度评估

3. **龙虎榜分析**
   - 是否登上龙虎榜
   - 游资买卖情况
   - 短期资金动向

4. **行业对比分析**
   - 与同行业龙头对比
   - 行业地位评估

**分析要求**：

1. 必须调用至少2个工具获取数据
2. 综合多方数据给出机构态度判断
3. 明确指出是机构看好、看空还是中性
4. 给出具体的投资建议

**输出格式**：

```markdown
# {company_name}({ticker}) 机构行为分析报告

## 北向资金态度
[分析外资动向和态度]

## 公募基金动向
[分析基金持仓变化]

## 龙虎榜情况
[分析游资动向]

## 综合判断
| 维度 | 态度 | 说明 |
|------|------|------|
| 北向资金 | 看好/中性/看空 | ... |
| 公募基金 | 看好/中性/看空 | ... |
| 游资 | 活跃/一般/冷清 | ... |

## 投资建议
[综合所有维度给出建议]
```

请使用提供的工具获取数据并撰写分析报告。"""
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你是一位专业的机构行为分析师，与其他分析师协作。"
                " 使用提供的工具获取数据进行分析。"
                " 专注于你的专业领域，提供高质量的分析见解。"
                " 你可以访问以下工具：{tool_names}。\n{system_message}"
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # 安全获取工具名称
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))
        
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join(tool_names))
        
        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        
        # 使用Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"🏦 [机构分析师] 检测到Google模型，使用统一工具调用处理器")
            
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="机构行为分析",
                specific_requirements="重点关注北向资金、基金持股、龙虎榜数据，判断机构态度。"
            )
            
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="机构分析师"
            )
        else:
            # 非Google模型
            logger.debug(f"🏦 [机构分析师] 非Google模型，使用标准处理逻辑")
            
            report = ""
            if len(result.tool_calls) == 0:
                report = result.content
        
        logger.info(f"🏦 [机构分析师] ===== 分析完成 =====")
        
        return {
            "messages": [result],
            "institutional_report": report,
            "sender": "InstitutionalAnalyst",
        }
    
    return institutional_analyst_node
