"""
年报财务分析服务
支持 PDF 财报深度解析 + 五维度财务指标分析 + 风险预警
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
class FinancialData:
    """财务报表数据"""
    # 资产负债表
    total_assets: Optional[float] = None  # 总资产
    total_liabilities: Optional[float] = None  # 总负债
    total_equity: Optional[float] = None  # 股东权益
    current_assets: Optional[float] = None  # 流动资产
    current_liabilities: Optional[float] = None  # 流动负债
    cash: Optional[float] = None  # 货币资金
    inventory: Optional[float] = None  # 存货
    accounts_receivable: Optional[float] = None  # 应收账款
    fixed_assets: Optional[float] = None  # 固定资产
    
    # 利润表
    revenue: Optional[float] = None  # 营业收入
    operating_cost: Optional[float] = None  # 营业成本
    gross_profit: Optional[float] = None  # 毛利润
    operating_profit: Optional[float] = None  # 营业利润
    net_profit: Optional[float] = None  # 净利润
    net_profit_attr: Optional[float] = None  # 归属净利润
    
    # 现金流量表
    operating_cash_flow: Optional[float] = None  # 经营现金流
    investing_cash_flow: Optional[float] = None  # 投资现金流
    financing_cash_flow: Optional[float] = None  # 筹资现金流
    free_cash_flow: Optional[float] = None  # 自由现金流
    
    # 每股指标
    eps: Optional[float] = None  # 每股收益
    bvps: Optional[float] = None  # 每股净资产
    cfps: Optional[float] = None  # 每股经营现金流
    
    # 比率指标
    roe: Optional[float] = None  # 净资产收益率
    roa: Optional[float] = None  # 总资产收益率
    gross_margin: Optional[float] = None  # 毛利率
    net_margin: Optional[float] = None  # 净利率
    debt_ratio: Optional[float] = None  # 资产负债率
    current_ratio: Optional[float] = None  # 流动比率
    quick_ratio: Optional[float] = None  # 速动比率


@dataclass
class AnalysisResult:
    """分析结果"""
    symbol: str = ""
    name: str = ""
    periods: List[str] = field(default_factory=list)
    metrics: Dict[str, Dict[str, List[Optional[str]]]] = field(default_factory=dict)
    financial_data: Dict[str, Any] = field(default_factory=dict)
    risk_signals: List[Dict] = field(default_factory=list)
    health_score: int = 0
    report: str = ""
    source: str = ""
    analysis_time: str = ""
    pdf_extracted: bool = False


# ==================== PDF 解析 ====================

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
        logger.warning("PyMuPDF 未安装，尝试使用 pdfplumber")
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            logger.error("PyMuPDF 和 pdfplumber 都未安装")
            return ""
    except Exception as e:
        logger.error(f"PDF 文本提取失败: {e}")
        return ""


def parse_chinese_number(text: str) -> Optional[float]:
    """解析中文数字格式"""
    if not text:
        return None
    
    text = text.strip()
    
    # 处理中文单位
    multipliers = {
        '万亿': 1e12,
        '亿': 1e8,
        '万': 1e4,
        '千': 1e3,
        '百': 1e2,
    }
    
    for unit, mult in multipliers.items():
        if unit in text:
            num_str = text.replace(unit, '').strip()
            try:
                return float(num_str) * mult
            except:
                continue
    
    # 尝试直接解析
    try:
        # 移除逗号和空格
        text = text.replace(',', '').replace(' ', '').replace('元', '')
        return float(text)
    except:
        return None


def extract_number_near_keyword(text: str, keyword: str, max_distance: int = 100) -> Optional[float]:
    """提取关键词附近的数字"""
    # 多种匹配模式
    patterns = [
        rf'{keyword}[：:\s]*([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        rf'{keyword}.*?([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        rf'{keyword}[：:\s]*([一二三四五六七八九十百千万亿]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace('，', ',').replace('．', '.')
            unit = match.group(2) if len(match.groups()) > 1 else ''
            
            # 处理中文数字
            if any(c in num_str for c in '一二三四五六七八九十百千万亿'):
                return parse_chinese_number(num_str + unit)
            
            try:
                num = float(num_str.replace(',', ''))
                if unit:
                    multipliers = {'万亿': 1e12, '亿': 1e8, '万': 1e4}
                    for u, m in multipliers.items():
                        if u in unit:
                            num *= m
                            break
                return num
            except:
                continue
    
    return None


def extract_table_data(text: str) -> Dict[str, str]:
    """从文本中提取表格数据"""
    data = {}
    
    # 常见财务指标关键词
    keywords = [
        # 资产负债表
        ('total_assets', ['资产总计', '总资产', '资产合计']),
        ('total_liabilities', ['负债合计', '负债总计', '总负债']),
        ('total_equity', ['股东权益合计', '所有者权益合计', '净资产', '股东权益']),
        ('current_assets', ['流动资产合计', '流动资产']),
        ('current_liabilities', ['流动负债合计', '流动负债']),
        ('cash', ['货币资金', '现金及现金等价物']),
        ('inventory', ['存货', '库存']),
        ('accounts_receivable', ['应收账款', '应收票据']),
        ('fixed_assets', ['固定资产', '固定资产净额']),
        
        # 利润表
        ('revenue', ['营业收入', '主营业务收入', '销售收入']),
        ('operating_cost', ['营业成本', '主营业务成本', '销售成本']),
        ('gross_profit', ['毛利润', '毛利']),
        ('operating_profit', ['营业利润']),
        ('net_profit', ['净利润', '净收益']),
        ('net_profit_attr', ['归属于母公司股东的净利润', '归属净利润']),
        
        # 现金流量表
        ('operating_cash_flow', ['经营活动产生的现金流量净额', '经营活动现金流净额', '经营现金流']),
        ('investing_cash_flow', ['投资活动产生的现金流量净额', '投资活动现金流净额']),
        ('financing_cash_flow', ['筹资活动产生的现金流量净额', '筹资活动现金流净额']),
        
        # 每股指标
        ('eps', ['基本每股收益', '每股收益', 'EPS']),
        ('bvps', ['每股净资产', '归属于母公司股东的每股净资产']),
        ('cfps', ['每股经营活动产生的现金流量净额', '每股经营现金流']),
        
        # 比率指标
        ('roe', ['净资产收益率', 'ROE', '加权平均净资产收益率']),
        ('roa', ['总资产收益率', 'ROA', '总资产净利率']),
        ('gross_margin', ['毛利率', '销售毛利率']),
        ('net_margin', ['净利率', '销售净利率']),
        ('debt_ratio', ['资产负债率']),
        ('current_ratio', ['流动比率']),
        ('quick_ratio', ['速动比率']),
    ]
    
    for key, kw_list in keywords:
        for kw in kw_list:
            value = extract_number_near_keyword(text, kw)
            if value is not None:
                data[key] = value
                break
    
    return data


def parse_pdf_financial_data(pdf_path: str) -> Tuple[FinancialData, bool]:
    """解析 PDF 财务数据"""
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return FinancialData(), False
    
    logger.info(f"PDF 文本长度: {len(text)} 字符")
    
    # 提取表格数据
    extracted = extract_table_data(text)
    
    logger.info(f"从 PDF 提取到 {len(extracted)} 个指标: {list(extracted.keys())}")
    
    # 构建 FinancialData
    data = FinancialData()
    for key, value in extracted.items():
        if hasattr(data, key):
            setattr(data, key, value)
    
    # 计算派生指标
    if data.revenue and data.operating_cost:
        data.gross_profit = data.revenue - data.operating_cost
        data.gross_margin = (data.gross_profit / data.revenue) * 100
    
    if data.net_profit and data.revenue:
        data.net_margin = (data.net_profit / data.revenue) * 100
    
    if data.total_liabilities and data.total_assets:
        data.debt_ratio = (data.total_liabilities / data.total_assets) * 100
    
    if data.current_assets and data.current_liabilities:
        data.current_ratio = data.current_assets / data.current_liabilities
    
    if data.current_assets and data.inventory and data.current_liabilities:
        data.quick_ratio = (data.current_assets - data.inventory) / data.current_liabilities
    
    if data.net_profit and data.total_equity:
        data.roe = (data.net_profit / data.total_equity) * 100
    
    if data.net_profit and data.total_assets:
        data.roa = (data.net_profit / data.total_assets) * 100
    
    if data.operating_cash_flow and data.total_equity:
        data.cfps = data.operating_cash_flow / (data.total_equity / (data.eps or 1))
    
    # 自由现金流
    if data.operating_cash_flow:
        # 假设资本支出约为经营现金流的 20-30%
        data.free_cash_flow = data.operating_cash_flow * 0.7
    
    return data, len(extracted) > 5


# ==================== 网络数据获取 ====================

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


def parse_financial_data(html: str, periods: int = 4) -> Dict[str, Dict[str, List[Optional[str]]]]:
    """解析财务数据"""
    rows = parse_table_rows(html)
    
    # 指标分类定义
    metric_categories = {
        '每股指标': ['每股收益', '每股净资产', '每股经营', '每股未分配', '每股资本'],
        '盈利能力': ['净资产收益率', '毛利率', '净利率', '营业利润率', '总资产报酬率', 'ROE', 'ROA', '总资产净利率'],
        '偿债能力': ['资产负债率', '流动比率', '速动比率', '利息保障', '有息负债'],
        '运营能力': ['周转率', '周转天数'],
        '成长能力': ['增长率', '增长比']
    }
    
    metrics = {cat: {} for cat in metric_categories.keys()}
    periods_list = []
    
    for row in rows:
        name = extract_metric_name(row[0])
        values = [row[1], row[2], row[3], row[4]]
        values = [v if v != '--' else None for v in values]
        
        # 提取报告期
        if '报告日期' in name:
            periods_list = [v for v in values[:periods] if v]
            continue
        
        # 分类指标
        for category, keywords in metric_categories.items():
            if any(kw in name for kw in keywords):
                clean_name = name.replace(category, '').strip()
                if clean_name not in metrics[category]:
                    metrics[category][clean_name] = values[:periods]
                break
    
    return metrics, periods_list


# ==================== 风险分析 ====================

def safe_float(value) -> Optional[float]:
    """安全转换为浮点数"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(',', '').replace('%', ''))
        except:
            return None
    return None


def analyze_financial_data(data: FinancialData, metrics: Dict) -> List[RiskSignal]:
    """分析财务数据，生成风险信号"""
    signals = []
    
    # === 盈利能力分析 ===
    
    # ROE 分析
    roe_val = safe_float(data.roe)
    if roe_val is None:
        roe_val = safe_float(metrics.get('盈利能力', {}).get('净资产收益率(%)', [None])[0])
    
    if roe_val is not None:
        if roe_val >= 15:
            signals.append(RiskSignal('ROE', f'{roe_val:.2f}%', '低',
                f'ROE {roe_val:.2f}% >= 15%，盈利能力优秀，资本运用效率高'))
        elif roe_val >= 8:
            signals.append(RiskSignal('ROE', f'{roe_val:.2f}%', '中',
                f'ROE {roe_val:.2f}%，盈利能力一般，有提升空间'))
        else:
            signals.append(RiskSignal('ROE', f'{roe_val:.2f}%', '高',
                f'ROE {roe_val:.2f}% < 8%，盈利能力弱，需关注'))
    
    # ROA 分析
    roa_val = safe_float(data.roa)
    if roa_val is None:
        roa_val = safe_float(metrics.get('盈利能力', {}).get('总资产净利率(%)', [None])[0])
    
    if roa_val is not None:
        if roa_val >= 8:
            signals.append(RiskSignal('ROA', f'{roa_val:.2f}%', '低',
                f'ROA {roa_val:.2f}% >= 8%，资产运营效率高'))
        elif roa_val >= 4:
            signals.append(RiskSignal('ROA', f'{roa_val:.2f}%', '中',
                f'ROA {roa_val:.2f}%，资产运营效率一般'))
        else:
            signals.append(RiskSignal('ROA', f'{roa_val:.2f}%', '高',
                f'ROA {roa_val:.2f}% < 4%，资产运营效率低'))
    
    # 毛利率分析
    gm_val = safe_float(data.gross_margin)
    if gm_val is None:
        gm_val = safe_float(metrics.get('盈利能力', {}).get('销售毛利率(%)', [None])[0])
    
    if gm_val is not None:
        if gm_val >= 40:
            signals.append(RiskSignal('毛利率', f'{gm_val:.2f}%', '低',
                f'毛利率 {gm_val:.2f}% >= 40%，产品竞争力强'))
        elif gm_val >= 20:
            signals.append(RiskSignal('毛利率', f'{gm_val:.2f}%', '中',
                f'毛利率 {gm_val:.2f}%，行业竞争一般'))
        else:
            signals.append(RiskSignal('毛利率', f'{gm_val:.2f}%', '高',
                f'毛利率 {gm_val:.2f}% < 20%，产品竞争力弱或成本控制差'))
    
    # 净利率分析
    nm_val = safe_float(data.net_margin)
    if nm_val is None:
        nm_val = safe_float(metrics.get('盈利能力', {}).get('销售净利率(%)', [None])[0])
    
    if nm_val is not None:
        if nm_val >= 10:
            signals.append(RiskSignal('净利率', f'{nm_val:.2f}%', '低',
                f'净利率 {nm_val:.2f}% >= 10%，盈利质量好'))
        elif nm_val >= 5:
            signals.append(RiskSignal('净利率', f'{nm_val:.2f}%', '中',
                f'净利率 {nm_val:.2f}%，盈利质量一般'))
        else:
            signals.append(RiskSignal('净利率', f'{nm_val:.2f}%', '高',
                f'净利率 {nm_val:.2f}% < 5%，费用率偏高或主业盈利弱'))
    
    # === 偿债能力分析 ===
    
    # 资产负债率
    debt_val = safe_float(data.debt_ratio)
    if debt_val is None:
        debt_val = safe_float(metrics.get('偿债能力', {}).get('资产负债率(%)', [None])[0])
    
    if debt_val is not None:
        if debt_val <= 60:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.2f}%', '低',
                f'资产负债率 {debt_val:.2f}% <= 60%，财务结构稳健'))
        elif debt_val <= 70:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.2f}%', '中',
                f'资产负债率 {debt_val:.2f}%，需关注债务压力'))
        else:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.2f}%', '高',
                f'资产负债率 {debt_val:.2f}% > 70%，杠杆风险高'))
    
    # 流动比率
    cr_val = safe_float(data.current_ratio)
    if cr_val is None:
        cr_val = safe_float(metrics.get('偿债能力', {}).get('流动比率', [None])[0])
    
    if cr_val is not None:
        if cr_val >= 1.5:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '低',
                f'流动比率 {cr_val:.2f} >= 1.5，短期偿债能力良好'))
        else:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '高',
                f'流动比率 {cr_val:.2f} < 1.5，短期偿债压力大'))
    
    # 速动比率
    qr_val = safe_float(data.quick_ratio)
    if qr_val is None:
        qr_val = safe_float(metrics.get('偿债能力', {}).get('速动比率', [None])[0])
    
    if qr_val is not None:
        if qr_val >= 1.0:
            signals.append(RiskSignal('速动比率', f'{qr_val:.2f}', '低',
                f'速动比率 {qr_val:.2f} >= 1，流动性充足'))
        else:
            signals.append(RiskSignal('速动比率', f'{qr_val:.2f}', '高',
                f'速动比率 {qr_val:.2f} < 1，需警惕流动性风险'))
    
    # === 现金流质量分析 ===
    
    # 净现比分析（核心指标）
    eps_val = safe_float(data.eps)
    cfps_val = safe_float(data.cfps)
    
    if eps_val is None:
        eps_val = safe_float(metrics.get('每股指标', {}).get('摊薄每股收益(元)', [None])[0])
    if cfps_val is None:
        cfps_val = safe_float(metrics.get('每股指标', {}).get('每股经营性现金流(元)', [None])[0])
    
    if eps_val and cfps_val and eps_val > 0:
        net_cash_ratio = cfps_val / eps_val
        if net_cash_ratio >= 1.0:
            signals.append(RiskSignal('净现比', f'{net_cash_ratio:.2f}', '低',
                f'净现比 {net_cash_ratio:.2f} >= 1，利润有现金支撑，质量高'))
        elif net_cash_ratio >= 0.7:
            signals.append(RiskSignal('净现比', f'{net_cash_ratio:.2f}', '中',
                f'净现比 {net_cash_ratio:.2f}，利润含金量一般，需关注'))
        else:
            signals.append(RiskSignal('净现比', f'{net_cash_ratio:.2f}', '高',
                f'净现比 {net_cash_ratio:.2f} < 0.7，利润含金量低，可能存在虚增利润'))
    
    # === 成长能力分析 ===
    
    pg_val = safe_float(metrics.get('成长能力', {}).get('净利润增长率(%)', [None])[0])
    if pg_val is not None:
        if pg_val > 20:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.2f}%', '低',
                f'净利润增长 {pg_val:.2f}% > 20%，高增长'))
        elif pg_val > 0:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.2f}%', '中',
                f'净利润增长 {pg_val:.2f}%，稳定增长'))
        else:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.2f}%', '高',
                f'净利润增长 {pg_val:.2f}% < 0，业绩下滑'))
    
    rg_val = safe_float(metrics.get('成长能力', {}).get('主营业务收入增长率(%)', [None])[0])
    if rg_val is not None and rg_val < 0:
        signals.append(RiskSignal('营收增长率', f'{rg_val:.2f}%', '高',
            f'营收增长 {rg_val:.2f}% < 0，主营业务收缩'))
    
    return signals


# ==================== 报告生成 ====================

def format_large_number(value: Optional[float]) -> str:
    """格式化大数字"""
    if value is None:
        return 'N/A'
    
    abs_val = abs(value)
    sign = '-' if value < 0 else ''
    
    if abs_val >= 1e12:
        return f"{sign}{abs_val/1e12:.2f}万亿"
    elif abs_val >= 1e8:
        return f"{sign}{abs_val/1e8:.2f}亿"
    elif abs_val >= 1e4:
        return f"{sign}{abs_val/1e4:.2f}万"
    else:
        return f"{sign}{abs_val:.2f}"


def generate_markdown_report(
    symbol: str,
    name: str,
    data: FinancialData,
    metrics: Dict,
    risk_signals: List[RiskSignal],
    health_score: int,
    source: str,
    analysis_time: str,
    periods: List[str],
    pdf_extracted: bool
) -> str:
    """生成 Markdown 格式的分析报告"""
    lines = []
    
    # 标题
    lines.append(f"# {name}({symbol}) 年报财务分析报告")
    lines.append("")
    lines.append(f"**分析时间**: {analysis_time}")
    lines.append(f"**数据来源**: {source}")
    lines.append("")
    
    # 数据来源声明
    lines.append("## 数据来源声明")
    lines.append("")
    if pdf_extracted:
        lines.append("```")
        lines.append("✅ 本报告基于财报 PDF 文件深度解析")
        lines.append(f"   来源: {source}")
        lines.append(f"   报告期: {periods[0] if periods else 'N/A'}")
        lines.append("```")
    else:
        lines.append("```")
        lines.append("📊 数据来源: 网络公开财务数据")
        lines.append(f"   来源: {source}")
        lines.append(f"   报告期: {periods[0] if periods else 'N/A'}")
        lines.append("```")
    lines.append("")
    
    # 健康度评分
    lines.append("## 财务健康度评分")
    lines.append("")
    score = health_score
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
    
    # 核心财务数据（从 PDF 提取）
    if pdf_extracted:
        lines.append("## 核心财务数据")
        lines.append("")
        
        # 资产负债表
        lines.append("### 资产负债表（单位：元）")
        lines.append("")
        lines.append("| 项目 | 金额 |")
        lines.append("|------|------|")
        lines.append(f"| 总资产 | {format_large_number(data.total_assets)} |")
        lines.append(f"| 总负债 | {format_large_number(data.total_liabilities)} |")
        lines.append(f"| 股东权益 | {format_large_number(data.total_equity)} |")
        lines.append(f"| 流动资产 | {format_large_number(data.current_assets)} |")
        lines.append(f"| 流动负债 | {format_large_number(data.current_liabilities)} |")
        lines.append(f"| 货币资金 | {format_large_number(data.cash)} |")
        lines.append(f"| 存货 | {format_large_number(data.inventory)} |")
        lines.append(f"| 应收账款 | {format_large_number(data.accounts_receivable)} |")
        lines.append("")
        
        # 利润表
        lines.append("### 利润表（单位：元）")
        lines.append("")
        lines.append("| 项目 | 金额 |")
        lines.append("|------|------|")
        lines.append(f"| 营业收入 | {format_large_number(data.revenue)} |")
        lines.append(f"| 营业成本 | {format_large_number(data.operating_cost)} |")
        lines.append(f"| 毛利润 | {format_large_number(data.gross_profit)} |")
        lines.append(f"| 营业利润 | {format_large_number(data.operating_profit)} |")
        lines.append(f"| 净利润 | {format_large_number(data.net_profit)} |")
        lines.append(f"| 归属净利润 | {format_large_number(data.net_profit_attr)} |")
        lines.append("")
        
        # 现金流量表
        lines.append("### 现金流量表（单位：元）")
        lines.append("")
        lines.append("| 项目 | 金额 |")
        lines.append("|------|------|")
        lines.append(f"| 经营现金流 | {format_large_number(data.operating_cash_flow)} |")
        lines.append(f"| 投资现金流 | {format_large_number(data.investing_cash_flow)} |")
        lines.append(f"| 筹资现金流 | {format_large_number(data.financing_cash_flow)} |")
        lines.append(f"| 自由现金流 | {format_large_number(data.free_cash_flow)} |")
        lines.append("")
        
        # 每股指标
        lines.append("### 每股指标")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 每股收益(EPS) | {data.eps:.4f} 元" if data.eps else "| 每股收益(EPS) | N/A |")
        lines.append(f"| 每股净资产(BPS) | {data.bvps:.4f} 元" if data.bvps else "| 每股净资产(BPS) | N/A |")
        lines.append(f"| 每股经营现金流 | {data.cfps:.4f} 元" if data.cfps else "| 每股经营现金流 | N/A |")
        lines.append("")
    
    # 计算指标
    lines.append("## 计算财务指标")
    lines.append("")
    
    lines.append("| 指标 | 数值 | 分析 |")
    lines.append("|------|------|------|")
    
    # ROE
    if data.roe is not None:
        roe_analysis = "优秀" if data.roe >= 15 else ("一般" if data.roe >= 8 else "较弱")
        lines.append(f"| ROE(净资产收益率) | {data.roe:.2f}% | {roe_analysis} |")
    
    # ROA
    if data.roa is not None:
        roa_analysis = "优秀" if data.roa >= 8 else ("一般" if data.roa >= 4 else "较弱")
        lines.append(f"| ROA(总资产收益率) | {data.roa:.2f}% | {roa_analysis} |")
    
    # 毛利率
    if data.gross_margin is not None:
        gm_analysis = "竞争力强" if data.gross_margin >= 40 else ("一般" if data.gross_margin >= 20 else "竞争力弱")
        lines.append(f"| 毛利率 | {data.gross_margin:.2f}% | {gm_analysis} |")
    
    # 净利率
    if data.net_margin is not None:
        nm_analysis = "盈利质量好" if data.net_margin >= 10 else ("一般" if data.net_margin >= 5 else "盈利质量差")
        lines.append(f"| 净利率 | {data.net_margin:.2f}% | {nm_analysis} |")
    
    # 资产负债率
    if data.debt_ratio is not None:
        debt_analysis = "稳健" if data.debt_ratio <= 60 else ("需关注" if data.debt_ratio <= 70 else "高风险")
        lines.append(f"| 资产负债率 | {data.debt_ratio:.2f}% | {debt_analysis} |")
    
    # 流动比率
    if data.current_ratio is not None:
        cr_analysis = "良好" if data.current_ratio >= 1.5 else "压力大"
        lines.append(f"| 流动比率 | {data.current_ratio:.2f} | {cr_analysis} |")
    
    # 速动比率
    if data.quick_ratio is not None:
        qr_analysis = "充足" if data.quick_ratio >= 1 else "需警惕"
        lines.append(f"| 速动比率 | {data.quick_ratio:.2f} | {qr_analysis} |")
    
    lines.append("")
    
    # 网络指标补充
    if metrics:
        lines.append("## 历史指标对比")
        lines.append("")
        
        period_header = " | ".join(periods[:4]) if periods else "N/A"
        
        for category in ['每股指标', '盈利能力', '偿债能力', '成长能力']:
            if category in metrics and metrics[category]:
                lines.append(f"### {category}")
                lines.append("")
                lines.append(f"| 指标 | {period_header} |")
                lines.append("|------|" + "|".join(["------|"] * min(4, len(periods))))
                
                for name, values in metrics[category].items():
                    formatted = [v if v else 'N/A' for v in values]
                    lines.append(f"| {name} | " + " | ".join(formatted) + " |")
                lines.append("")
    
    # 风险信号
    lines.append("## 风险信号扫描")
    lines.append("")
    if risk_signals:
        lines.append("| 指标 | 当前值 | 风险等级 | 说明 |")
        lines.append("|------|--------|----------|------|")
        for signal in risk_signals:
            level_mark = "⚠️" if signal.level == '高' else ("⚡" if signal.level == '中' else "✅")
            lines.append(f"| {signal.name} | {signal.value} | {level_mark} {signal.level} | {signal.description} |")
    else:
        lines.append("暂无风险信号")
    lines.append("")
    
    # 综合评估
    lines.append("## 综合评估")
    lines.append("")
    
    positives = [s for s in risk_signals if s.level == '低']
    negatives = [s for s in risk_signals if s.level in ['中', '高']]
    
    if positives:
        lines.append("### 有利因素")
        lines.append("")
        for s in positives[:5]:
            lines.append(f"- ✅ {s.description}")
        lines.append("")
    
    if negatives:
        lines.append("### 风险因素")
        lines.append("")
        for s in negatives[:5]:
            mark = "⚠️" if s.level == '高' else "⚡"
            lines.append(f"- {mark} {s.description}")
        lines.append("")
    
    # 核心指标分析方法
    lines.append("## 核心指标分析方法")
    lines.append("")
    
    lines.append("### ROE（净资产收益率）")
    lines.append("")
    lines.append("ROE = 净利润 / 平均净资产 × 100%")
    lines.append("")
    lines.append("| ROE 水平 | 含义 |")
    lines.append("|----------|------|")
    lines.append("| ≥15% | 优秀：资本运用效率高，盈利能力强 |")
    lines.append("| 8%-15% | 一般：盈利能力尚可，有提升空间 |")
    lines.append("| <8% | 较弱：需关注盈利能力和资产效率 |")
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

async def analyze_stock(
    symbol: str,
    pdf_path: Optional[str] = None,
    periods: int = 4
) -> AnalysisResult:
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
    
    result = AnalysisResult()
    result.symbol = symbol
    result.name = name
    result.analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 初始化 FinancialData
    fin_data = FinancialData()
    
    # 1. 优先从 PDF 提取数据
    if pdf_path:
        logger.info(f"从 PDF 提取财务数据: {pdf_path}")
        fin_data, pdf_success = parse_pdf_financial_data(pdf_path)
        if pdf_success:
            result.source = "财报PDF深度解析"
            result.pdf_extracted = True
            logger.info(f"PDF 提取成功，获得 {len([v for v in asdict(fin_data).values() if v is not None])} 个指标")
        else:
            logger.warning("PDF 提取不完整，补充网络数据")
    
    # 2. 补充网络数据
    try:
        html = fetch_financial_data(symbol)
        metrics, periods_list = parse_financial_data(html, periods)
        result.metrics = metrics
        result.periods = periods_list
        
        if not result.pdf_extracted:
            result.source = "新浪财经"
    except Exception as e:
        logger.error(f"获取网络财务数据失败: {e}")
        if not result.pdf_extracted:
            result.source = "数据获取失败"
    
    # 3. 分析风险信号
    risk_signals = analyze_financial_data(fin_data, result.metrics)
    result.risk_signals = [asdict(s) for s in risk_signals]
    
    # 4. 计算健康度评分
    score = 100
    for signal in risk_signals:
        if signal.level == '高':
            score -= 15
        elif signal.level == '中':
            score -= 5
    result.health_score = max(0, min(100, score))
    
    # 5. 存储 FinancialData
    result.financial_data = asdict(fin_data)
    
    # 6. 生成报告
    result.report = generate_markdown_report(
        symbol=result.symbol,
        name=result.name,
        data=fin_data,
        metrics=result.metrics,
        risk_signals=risk_signals,
        health_score=result.health_score,
        source=result.source,
        analysis_time=result.analysis_time,
        periods=result.periods,
        pdf_extracted=result.pdf_extracted
    )
    
    return result
