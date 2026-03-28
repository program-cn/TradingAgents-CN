"""
年报财务分析服务
参考 OpenClaw annual-report-analyzer skill 实现
支持：五维度财务指标分析、现金流质量、财务造假信号识别、风险预警
"""

import re
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== 数据结构 ====================

@dataclass
class RiskSignal:
    """风险信号"""
    name: str
    value: str
    level: str  # 低/中/高
    description: str


@dataclass
class FinancialMetrics:
    """财务指标数据"""
    category: str
    name: str
    values: List[Optional[str]]
    unit: str = ""


@dataclass
class AnalysisResult:
    """分析结果"""
    symbol: str = ""
    name: str = ""
    periods: List[str] = field(default_factory=list)
    metrics: Dict[str, Dict[str, List[Optional[str]]]] = field(default_factory=dict)
    risk_signals: List[Dict] = field(default_factory=list)
    health_score: int = 0
    report: str = ""
    source: str = ""
    analysis_time: str = ""


# ==================== 数据获取 ====================

def fetch_financial_data(symbol: str) -> str:
    """从新浪财经获取财务数据HTML"""
    url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/{symbol}/displaytype/4.phtml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('gbk', errors='ignore')
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络请求失败: {e}")


def fetch_stock_info(symbol: str) -> Tuple[str, float, float]:
    """获取股票名称和实时价格"""
    url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=0.{symbol}&fields=f58,f43,f44"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'data' in result and result['data']:
                d = result['data']
                name = d.get('f58', symbol)
                price = d.get('f43', 0) / 100 if d.get('f43') else 0
                change = d.get('f44', 0) / 100 if d.get('f44') else 0
                return name, price, change
    except Exception as e:
        logger.warning(f"获取股票信息失败: {e}")
    return symbol, 0, 0


def parse_table_rows(html: str) -> List[tuple]:
    """解析HTML表格数据"""
    pattern = r'<tr><td[^>]*>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>'
    return re.findall(pattern, html, re.DOTALL)


def extract_metric_name(cell: str) -> str:
    """提取指标名称，去除HTML标签"""
    return re.sub(r'<[^>]+>', '', cell).strip()


# ==================== PDF 文本提取 ====================

def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 提取文本内容"""
    try:
        import fitz  # PyMuPDF
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except ImportError:
        logger.warning("PyMuPDF 未安装，跳过 PDF 文本提取")
        return ""
    except Exception as e:
        logger.error(f"PDF 文本提取失败: {e}")
        return ""


def extract_metrics_from_pdf_text(text: str) -> Dict[str, Any]:
    """从 PDF 文本中提取财务指标"""
    metrics = {}
    
    # 每股收益
    eps_match = re.search(r'基本每股收益[：:\s]*([0-9.-]+)', text)
    if eps_match:
        metrics['eps'] = float(eps_match.group(1))
    
    # 每股净资产
    bvps_match = re.search(r'每股净资产[：:\s]*([0-9.-]+)', text)
    if bvps_match:
        metrics['bvps'] = float(bvps_match.group(1))
    
    # 净资产收益率
    roe_match = re.search(r'净资产收益率[：:\s]*([0-9.-]+)%?', text)
    if roe_match:
        metrics['roe'] = float(roe_match.group(1))
    
    # 毛利率
    gross_match = re.search(r'毛利率[：:\s]*([0-9.-]+)%?', text)
    if gross_match:
        metrics['gross_margin'] = float(gross_match.group(1))
    
    # 净利率
    net_match = re.search(r'净利率[：:\s]*([0-9.-]+)%?', text)
    if net_match:
        metrics['net_margin'] = float(net_match.group(1))
    
    return metrics


# ==================== 数据解析 ====================

def parse_financial_data(html: str, periods: int = 4) -> AnalysisResult:
    """解析财务数据"""
    rows = parse_table_rows(html)
    
    result = AnalysisResult()
    
    # 指标分类定义
    metric_categories = {
        '每股指标': ['每股收益', '每股净资产', '每股经营', '每股未分配', '每股资本'],
        '盈利能力': ['净资产收益率', '毛利率', '净利率', '营业利润率', '总资产报酬率', 'ROE', 'ROA', '总资产净利率'],
        '偿债能力': ['资产负债率', '流动比率', '速动比率', '利息保障', '有息负债'],
        '运营能力': ['周转率', '周转天数'],
        '成长能力': ['增长率', '增长比']
    }
    
    result.metrics = {cat: {} for cat in metric_categories.keys()}
    
    for row in rows:
        name = extract_metric_name(row[0])
        values = [row[1], row[2], row[3], row[4]]
        values = [v if v != '--' else None for v in values]
        
        # 提取报告期
        if '报告日期' in name:
            result.periods = [v for v in values[:periods] if v]
            continue
        
        # 分类指标
        for category, keywords in metric_categories.items():
            if any(kw in name for kw in keywords):
                clean_name = name.replace(category, '').strip()
                if clean_name not in result.metrics[category]:
                    result.metrics[category][clean_name] = values[:periods]
                break
    
    return result


# ==================== 风险分析 ====================

def safe_float(value: Optional[str]) -> Optional[float]:
    """安全转换为浮点数"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None


def analyze_cash_flow_quality(result: AnalysisResult) -> List[RiskSignal]:
    """分析现金流质量 - 净现比是识别财务造假的核心指标"""
    signals = []
    
    eps = result.metrics.get('每股指标', {}).get('摊薄每股收益(元)', [None])
    cfps = result.metrics.get('每股指标', {}).get('每股经营性现金流(元)', [None])
    
    eps_val = safe_float(eps[0]) if eps else None
    cfps_val = safe_float(cfps[0]) if cfps else None
    
    if eps_val and cfps_val and eps_val > 0:
        net_cash_ratio = cfps_val / eps_val
        if net_cash_ratio >= 1.0:
            signals.append(RiskSignal('净现比', f'{net_cash_ratio:.2f}', '低',
                f'净现比{net_cash_ratio:.2f}>1，利润有现金支撑，质量高'))
        elif net_cash_ratio >= 0.7:
            signals.append(RiskSignal('净现比', f'{net_cash_ratio:.2f}', '中',
                f'净现比{net_cash_ratio:.2f}，利润含金量一般，需关注'))
        else:
            signals.append(RiskSignal('净现比', f'{net_cash_ratio:.2f}', '高',
                f'净现比{net_cash_ratio:.2f}<0.7，利润含金量低，可能存在虚增利润'))
    
    return signals


def analyze_profitability(result: AnalysisResult) -> List[RiskSignal]:
    """分析盈利能力 - ROE是核心指标"""
    signals = []
    
    # ROE 分析
    roe = result.metrics.get('盈利能力', {}).get('净资产收益率(%)', [None])
    roe_val = safe_float(roe[0]) if roe else None
    
    if roe_val is not None:
        if roe_val >= 15:
            signals.append(RiskSignal('ROE', f'{roe_val:.1f}%', '低',
                f'ROE {roe_val:.1f}%>=15%，盈利能力优秀，资本运用效率高'))
        elif roe_val >= 8:
            signals.append(RiskSignal('ROE', f'{roe_val:.1f}%', '中',
                f'ROE {roe_val:.1f}%，盈利能力一般，有提升空间'))
        else:
            signals.append(RiskSignal('ROE', f'{roe_val:.1f}%', '高',
                f'ROE {roe_val:.1f}%<8%，盈利能力弱，需关注'))
    
    # 毛利率分析
    gross_margin = result.metrics.get('盈利能力', {}).get('销售毛利率(%)', [None])
    gm_val = safe_float(gross_margin[0]) if gross_margin else None
    
    if gm_val is not None:
        if gm_val >= 40:
            signals.append(RiskSignal('毛利率', f'{gm_val:.1f}%', '低',
                f'毛利率{gm_val:.1f}%>=40%，产品竞争力强'))
        elif gm_val >= 20:
            signals.append(RiskSignal('毛利率', f'{gm_val:.1f}%', '中',
                f'毛利率{gm_val:.1f}%，行业竞争一般'))
        else:
            signals.append(RiskSignal('毛利率', f'{gm_val:.1f}%', '高',
                f'毛利率{gm_val:.1f}%<20%，产品竞争力弱或成本控制差'))
    
    # 净利率分析
    net_margin = result.metrics.get('盈利能力', {}).get('销售净利率(%)', [None])
    nm_val = safe_float(net_margin[0]) if net_margin else None
    
    if nm_val is not None:
        if nm_val >= 10:
            signals.append(RiskSignal('净利率', f'{nm_val:.1f}%', '低',
                f'净利率{nm_val:.1f}%>=10%，盈利质量好'))
        elif nm_val >= 5:
            signals.append(RiskSignal('净利率', f'{nm_val:.1f}%', '中',
                f'净利率{nm_val:.1f}%，盈利质量一般'))
        else:
            signals.append(RiskSignal('净利率', f'{nm_val:.1f}%', '高',
                f'净利率{nm_val:.1f}%<5%，费用率偏高或主业盈利弱'))
    
    # ROA 分析
    roa = result.metrics.get('盈利能力', {}).get('总资产净利率(%)', [None])
    roa_val = safe_float(roa[0]) if roa else None
    
    if roa_val is not None:
        if roa_val >= 8:
            signals.append(RiskSignal('ROA', f'{roa_val:.1f}%', '低',
                f'ROA {roa_val:.1f}%>=8%，资产运营效率高'))
        elif roa_val >= 4:
            signals.append(RiskSignal('ROA', f'{roa_val:.1f}%', '中',
                f'ROA {roa_val:.1f}%，资产运营效率一般'))
        else:
            signals.append(RiskSignal('ROA', f'{roa_val:.1f}%', '高',
                f'ROA {roa_val:.1f}%<4%，资产运营效率低'))
    
    return signals


def analyze_solvency(result: AnalysisResult) -> List[RiskSignal]:
    """分析偿债能力"""
    signals = []
    
    # 资产负债率
    debt_ratio = result.metrics.get('偿债能力', {}).get('资产负债率(%)', [None])
    debt_val = safe_float(debt_ratio[0]) if debt_ratio else None
    
    if debt_val is not None:
        if debt_val <= 60:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.1f}%', '低',
                f'资产负债率{debt_val:.1f}%<=60%，财务结构稳健'))
        elif debt_val <= 70:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.1f}%', '中',
                f'资产负债率{debt_val:.1f}%，需关注债务压力'))
        else:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.1f}%', '高',
                f'资产负债率{debt_val:.1f}%>70%，杠杆风险高'))
    
    # 流动比率
    current_ratio = result.metrics.get('偿债能力', {}).get('流动比率', [None])
    cr_val = safe_float(current_ratio[0]) if current_ratio else None
    
    if cr_val is not None:
        if cr_val >= 1.5:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '低',
                f'流动比率{cr_val:.2f}>=1.5，短期偿债能力良好'))
        else:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '高',
                f'流动比率{cr_val:.2f}<1.5，短期偿债压力大'))
    
    # 速动比率
    quick_ratio = result.metrics.get('偿债能力', {}).get('速动比率', [None])
    qr_val = safe_float(quick_ratio[0]) if quick_ratio else None
    
    if qr_val is not None:
        if qr_val >= 1.0:
            signals.append(RiskSignal('速动比率', f'{qr_val:.2f}', '低',
                f'速动比率{qr_val:.2f}>=1，流动性充足'))
        else:
            signals.append(RiskSignal('速动比率', f'{qr_val:.2f}', '高',
                f'速动比率{qr_val:.2f}<1，需警惕流动性风险'))
    
    return signals


def analyze_growth(result: AnalysisResult) -> List[RiskSignal]:
    """分析成长能力"""
    signals = []
    
    # 净利润增长率
    profit_growth = result.metrics.get('成长能力', {}).get('净利润增长率(%)', [None])
    pg_val = safe_float(profit_growth[0]) if profit_growth else None
    
    if pg_val is not None:
        if pg_val > 20:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.1f}%', '低',
                f'净利润增长{pg_val:.1f}%>20%，高增长'))
        elif pg_val > 0:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.1f}%', '中',
                f'净利润增长{pg_val:.1f}%，稳定增长'))
        else:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.1f}%', '高',
                f'净利润增长{pg_val:.1f}%<0，业绩下滑'))
    
    # 营收增长率
    revenue_growth = result.metrics.get('成长能力', {}).get('主营业务收入增长率(%)', [None])
    rg_val = safe_float(revenue_growth[0]) if revenue_growth else None
    
    if rg_val is not None:
        if rg_val < 0:
            signals.append(RiskSignal('营收增长率', f'{rg_val:.1f}%', '高',
                f'营收增长{rg_val:.1f}%<0，主营业务收缩'))
        elif rg_val > 30:
            signals.append(RiskSignal('营收增长率', f'{rg_val:.1f}%', '低',
                f'营收增长{rg_val:.1f}%，高速扩张'))
    
    return signals


def analyze_operation(result: AnalysisResult) -> List[RiskSignal]:
    """分析运营能力"""
    signals = []
    
    # 应收账款周转率
    ar_turnover = result.metrics.get('运营能力', {}).get('应收账款周转率(次)', [None])
    ar_val = safe_float(ar_turnover[0]) if ar_turnover else None
    
    if ar_val is not None:
        if ar_val >= 6:
            signals.append(RiskSignal('应收账款周转率', f'{ar_val:.1f}次', '低',
                f'应收账款周转率{ar_val:.1f}次，回款效率高'))
        elif ar_val < 3:
            signals.append(RiskSignal('应收账款周转率', f'{ar_val:.1f}次', '中',
                f'应收账款周转率{ar_val:.1f}次较低，回款周期长'))
    
    # 存货周转率
    inv_turnover = result.metrics.get('运营能力', {}).get('存货周转率(次)', [None])
    inv_val = safe_float(inv_turnover[0]) if inv_turnover else None
    
    if inv_val is not None:
        if inv_val >= 3:
            signals.append(RiskSignal('存货周转率', f'{inv_val:.1f}次', '低',
                f'存货周转率{inv_val:.1f}次，库存周转良好'))
        elif inv_val < 1:
            signals.append(RiskSignal('存货周转率', f'{inv_val:.2f}次', '中',
                f'存货周转率{inv_val:.2f}次较低，库存周转慢'))
    
    return signals


def run_risk_analysis(result: AnalysisResult) -> None:
    """运行完整风险分析"""
    signals = []
    signals.extend(analyze_cash_flow_quality(result))
    signals.extend(analyze_profitability(result))
    signals.extend(analyze_solvency(result))
    signals.extend(analyze_growth(result))
    signals.extend(analyze_operation(result))
    
    result.risk_signals = [asdict(s) for s in signals]
    
    # 计算健康度评分
    score = 100
    for signal in signals:
        if signal.level == '高':
            score -= 15
        elif signal.level == '中':
            score -= 5
    result.health_score = max(0, min(100, score))


# ==================== 报告生成 ====================

def format_value(value: Optional[str], suffix: str = '') -> str:
    """格式化数值显示"""
    if value is None or value == '':
        return 'N/A'
    try:
        num = float(value)
        if suffix == '%' or suffix == '倍':
            return f"{num:.2f}{suffix}"
        if abs(num) >= 1e8:
            return f"{num/1e8:.2f}亿"
        elif abs(num) >= 1e4:
            return f"{num/1e4:.2f}万"
        else:
            formatted = f"{num:.4f}".rstrip('0').rstrip('.')
            return formatted + suffix if suffix else formatted
    except ValueError:
        return value + suffix if suffix else value


def generate_markdown_report(result: AnalysisResult) -> str:
    """生成 Markdown 格式的分析报告"""
    lines = []
    
    # 标题
    lines.append(f"# {result.name}({result.symbol}) 年报财务分析报告")
    lines.append("")
    lines.append(f"**分析时间**: {result.analysis_time}")
    lines.append(f"**数据来源**: {result.source}")
    lines.append("")
    
    # 数据来源声明
    lines.append("## 数据来源声明")
    lines.append("")
    lines.append("```")
    lines.append(f"📊 数据来源: {result.source}")
    lines.append(f"📅 报告期: {result.periods[0] if result.periods else 'N/A'}")
    lines.append("```")
    lines.append("")
    
    # 健康度评分
    lines.append("## 财务健康度评分")
    lines.append("")
    score = result.health_score
    if score >= 80:
        emoji = "🟢"
        status = "健康"
    elif score >= 60:
        emoji = "🟡"
        status = "一般"
    else:
        emoji = "🔴"
        status = "风险"
    lines.append(f"**{emoji} {score}/100 - {status}**")
    lines.append("")
    
    # 关键指标
    lines.append("## 核心财务指标")
    lines.append("")
    
    periods = result.periods or ['N/A', 'N/A', 'N/A', 'N/A']
    
    # 每股指标
    if '每股指标' in result.metrics and result.metrics['每股指标']:
        lines.append("### 每股指标")
        lines.append("")
        lines.append("| 指标 | " + " | ".join(periods[:4]) + " |")
        lines.append("|------|" + "|".join(["------|"] * min(4, len(periods))))
        for name, values in result.metrics['每股指标'].items():
            formatted = [format_value(v) for v in values]
            lines.append(f"| {name} | " + " | ".join(formatted) + " |")
        lines.append("")
    
    # 盈利能力
    if '盈利能力' in result.metrics and result.metrics['盈利能力']:
        lines.append("### 盈利能力")
        lines.append("")
        lines.append("| 指标 | " + " | ".join(periods[:4]) + " |")
        lines.append("|------|" + "|".join(["------|"] * min(4, len(periods))))
        for name, values in result.metrics['盈利能力'].items():
            formatted = [format_value(v) for v in values]
            lines.append(f"| {name} | " + " | ".join(formatted) + " |")
        lines.append("")
    
    # 偿债能力
    if '偿债能力' in result.metrics and result.metrics['偿债能力']:
        lines.append("### 偿债能力")
        lines.append("")
        lines.append("| 指标 | " + " | ".join(periods[:4]) + " |")
        lines.append("|------|" + "|".join(["------|"] * min(4, len(periods))))
        for name, values in result.metrics['偿债能力'].items():
            formatted = [format_value(v) for v in values]
            lines.append(f"| {name} | " + " | ".join(formatted) + " |")
        lines.append("")
    
    # 成长能力
    if '成长能力' in result.metrics and result.metrics['成长能力']:
        lines.append("### 成长能力")
        lines.append("")
        lines.append("| 指标 | " + " | ".join(periods[:4]) + " |")
        lines.append("|------|" + "|".join(["------|"] * min(4, len(periods))))
        for name, values in result.metrics['成长能力'].items():
            formatted = [format_value(v) for v in values]
            lines.append(f"| {name} | " + " | ".join(formatted) + " |")
        lines.append("")
    
    # 风险信号
    lines.append("## 风险信号扫描")
    lines.append("")
    if result.risk_signals:
        lines.append("| 指标 | 当前值 | 风险等级 | 说明 |")
        lines.append("|------|--------|----------|------|")
        for signal in result.risk_signals:
            level_mark = "⚠️" if signal['level'] == '高' else ("⚡" if signal['level'] == '中' else "✅")
            lines.append(f"| {signal['name']} | {signal['value']} | {level_mark} {signal['level']} | {signal['description']} |")
    else:
        lines.append("暂无风险信号")
    lines.append("")
    
    # 综合评估
    lines.append("## 综合评估")
    lines.append("")
    
    positives = [s for s in result.risk_signals if s['level'] == '低']
    negatives = [s for s in result.risk_signals if s['level'] in ['中', '高']]
    
    if positives:
        lines.append("### 有利因素")
        lines.append("")
        for s in positives[:5]:
            lines.append(f"- ✅ {s['description']}")
        lines.append("")
    
    if negatives:
        lines.append("### 风险因素")
        lines.append("")
        for s in negatives[:5]:
            mark = "⚠️" if s['level'] == '高' else "⚡"
            lines.append(f"- {mark} {s['description']}")
        lines.append("")
    
    # 核心指标分析方法
    lines.append("## 核心指标分析方法")
    lines.append("")
    lines.append("### ROE（净资产收益率）分析")
    lines.append("")
    lines.append("ROE = 净利润 / 平均净资产 × 100%")
    lines.append("")
    lines.append("| ROE 水平 | 含义 |")
    lines.append("|----------|------|")
    lines.append("| ≥15% | 优秀：资本运用效率高，盈利能力强 |")
    lines.append("| 8%-15% | 一般：盈利能力尚可，有提升空间 |")
    lines.append("| <8% | 较弱：需关注盈利能力和资产效率 |")
    lines.append("")
    
    lines.append("### 毛利率与净利率分析")
    lines.append("")
    lines.append("- **毛利率** = (营业收入 - 营业成本) / 营业收入 × 100%")
    lines.append("- **净利率** = 净利润 / 营业收入 × 100%")
    lines.append("")
    lines.append("毛利率反映产品竞争力，净利率反映整体盈利能力。两者差距反映费用控制水平。")
    lines.append("")
    
    lines.append("### 净现比（现金流质量）")
    lines.append("")
    lines.append("净现比 = 经营现金流净额 / 净利润")
    lines.append("")
    lines.append("| 净现比 | 含义 |")
    lines.append("|--------|------|")
    lines.append("| ≥1.0 | 健康：利润有现金支撑 |")
    lines.append("| 0.7-1.0 | 关注：利润含金量一般 |")
    lines.append("| <0.7 | 预警：利润含金量低，可能存在虚增 |")
    lines.append("")
    lines.append("**马氏定律**: 长期净现比低于0.7，可能存在利润造假。")
    lines.append("")
    
    # 风险提示
    lines.append("## 风险提示")
    lines.append("")
    lines.append("1. 本分析基于公开财务数据，可能存在信息滞后或不完整的情况。")
    lines.append("2. 财务指标异常不代表一定存在问题，需结合行业特性和公司战略综合判断。")
    lines.append("3. 投资有风险，决策需谨慎，本报告不构成投资建议。")
    
    return "\n".join(lines)


# ==================== 主分析函数 ====================

async def analyze_stock(symbol: str, pdf_path: Optional[str] = None, periods: int = 4) -> AnalysisResult:
    """
    分析股票财务数据
    
    Args:
        symbol: 股票代码
        pdf_path: PDF 文件路径（可选）
        periods: 报告期数量
    
    Returns:
        AnalysisResult: 分析结果
    """
    symbol = symbol.zfill(6)
    
    # 获取股票信息
    name, price, change = fetch_stock_info(symbol)
    
    # 获取财务数据
    html = fetch_financial_data(symbol)
    result = parse_financial_data(html, periods)
    result.symbol = symbol
    result.name = name
    result.analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 确定数据来源
    if pdf_path:
        result.source = "财报PDF + 新浪财经"
        # 尝试从 PDF 提取补充信息
        pdf_text = extract_text_from_pdf(pdf_path)
        if pdf_text:
            pdf_metrics = extract_metrics_from_pdf_text(pdf_text)
            logger.info(f"从PDF提取指标: {pdf_metrics}")
    else:
        result.source = "新浪财经"
    
    # 运行风险分析
    run_risk_analysis(result)
    
    # 生成报告
    result.report = generate_markdown_report(result)
    
    return result
