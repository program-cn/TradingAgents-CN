#!/usr/bin/env python3
"""
API 密钥和模型测试脚本
测试 LLM 提供商和数据源的连接状态

用法:
    python test_model_token.py              # 测试所有配置
    python test_model_token.py --deepseek   # 仅测试 DeepSeek
    python test_model_token.py --dashscope  # 仅测试阿里百炼
    python test_model_token.py --moonshot   # 仅测试 Kimi (月之暗面)
    python test_model_token.py --tushare    # 仅测试 Tushare
"""

import os
import sys
import argparse
import requests
from pathlib import Path

# 颜色输出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(title):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def is_placeholder(value, key_name=""):
    """检查是否为占位符"""
    if not value:
        return True
    placeholders = [
        "your_", "xxx", "placeholder", "sk-demo", "sk-test",
        "your-api-key", "your_token", "change_me"
    ]
    value_lower = value.lower()
    for ph in placeholders:
        if ph in value_lower:
            return True
    # 检查是否太短
    if len(value) < 20:
        return True
    return False


def load_env_file():
    """加载 .env 文件"""
    env_paths = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path.home() / "tradingagents-demo" / ".env",
    ]
    
    env_found = False
    for env_path in env_paths:
        if env_path.exists():
            print_info(f"加载环境文件: {env_path}")
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        os.environ.setdefault(key.strip(), value.strip().strip('"\''))
            env_found = True
            break
    
    if not env_found:
        print_warning("未找到 .env 文件，使用系统环境变量")
    
    return env_found


def test_deepseek():
    """测试 DeepSeek API"""
    print_header("测试 DeepSeek API")
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    enabled = os.getenv("DEEPSEEK_ENABLED", "true").lower() == "true"
    
    # 检查是否启用
    if not enabled:
        print_warning("DeepSeek 未启用 (DEEPSEEK_ENABLED=false)")
        return False
    
    # 检查 API Key
    print_info(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    
    if is_placeholder(api_key, "DEEPSEEK_API_KEY"):
        print_error("DEEPSEEK_API_KEY 未配置或为占位符")
        print_info("获取地址: https://platform.deepseek.com/")
        return False
    
    # 测试 API 连接
    print_info("正在测试 API 连接...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 简单的测试请求
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("DeepSeek API 连接成功!")
            print_info(f"模型: deepseek-chat 可用")
            
            # 测试其他模型
            models_to_test = ["deepseek-reasoner"]
            for model in models_to_test:
                try:
                    payload["model"] = model
                    resp = requests.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    if resp.status_code == 200:
                        print_success(f"模型 {model} 可用")
                    else:
                        print_warning(f"模型 {model} 不可用: {resp.status_code}")
                except Exception as e:
                    print_warning(f"模型 {model} 测试失败: {str(e)[:50]}")
            
            return True
        elif response.status_code == 401:
            print_error("API Key 无效或已过期")
            print_info("请检查 DEEPSEEK_API_KEY 是否正确")
            return False
        elif response.status_code == 429:
            print_warning("API 请求频率限制或余额不足")
            print_info("请检查账户余额: https://platform.deepseek.com/usage")
            return False
        else:
            print_error(f"API 请求失败: HTTP {response.status_code}")
            print_info(f"响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到 DeepSeek API，请检查网络")
        return False
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_dashscope():
    """测试阿里百炼 API"""
    print_header("测试阿里百炼 (DashScope) API")
    
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    enabled = os.getenv("DASHSCOPE_ENABLED", "true").lower() == "true"
    
    # 检查是否启用
    if not enabled:
        print_warning("阿里百炼未启用 (DASHSCOPE_ENABLED=false)")
        return False
    
    # 检查 API Key
    print_info(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    
    if is_placeholder(api_key, "DASHSCOPE_API_KEY"):
        print_error("DASHSCOPE_API_KEY 未配置或为占位符")
        print_info("获取地址: https://dashscope.aliyun.com/")
        return False
    
    # 测试 API 连接
    print_info("正在测试 API 连接...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 测试 qwen-turbo（快速模型）
        payload = {
            "model": "qwen-turbo",
            "input": {
                "messages": [{"role": "user", "content": "Hi"}]
            },
            "parameters": {
                "max_tokens": 5
            }
        }
        
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("阿里百炼 API 连接成功!")
            print_info(f"模型: qwen-turbo 可用")
            
            # 检查账户状态
            print_info("测试 qwen3-max 模型...")
            payload["model"] = "qwen3-max"
            resp = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                print_success("模型 qwen3-max 可用")
            elif resp.status_code == 400:
                error_data = resp.json()
                error_code = error_data.get("code", "")
                if error_code == "Arrearage":
                    print_error("账户欠费! 请充值后继续使用")
                    print_info("充值地址: https://account.aliyun.com/")
                    return False
                else:
                    print_warning(f"模型 qwen3-max 不可用: {error_code}")
            else:
                print_warning(f"模型 qwen3-max 测试失败: {resp.status_code}")
            
            return True
        elif response.status_code == 400:
            error_data = response.json()
            error_code = error_data.get("code", "")
            if error_code == "Arrearage":
                print_error("账户欠费! 请充值后继续使用")
                print_info("充值地址: https://account.aliyun.com/")
            elif error_code == "InvalidApiKey":
                print_error("API Key 无效")
            else:
                print_error(f"API 错误: {error_code}")
            return False
        elif response.status_code == 401:
            print_error("API Key 无效或已过期")
            return False
        else:
            print_error(f"API 请求失败: HTTP {response.status_code}")
            print_info(f"响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到阿里云 API，请检查网络")
        return False
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_tushare():
    """测试 Tushare Token"""
    print_header("测试 Tushare 数据源")
    
    token = os.getenv("TUSHARE_TOKEN", "")
    enabled = os.getenv("TUSHARE_ENABLED", "true").lower() == "true"
    
    # 检查是否启用
    if not enabled:
        print_warning("Tushare 未启用 (TUSHARE_ENABLED=false)")
        return False
    
    # 检查 Token
    print_info(f"Token: {token[:8]}...{token[-4:] if len(token) > 12 else '***'}")
    
    if is_placeholder(token, "TUSHARE_TOKEN"):
        print_error("TUSHARE_TOKEN 未配置或为占位符")
        print_info("获取地址: https://tushare.pro/register")
        return False
    
    # 测试 API 连接
    print_info("正在测试 Tushare API 连接...")
    
    try:
        # 使用 trade_calendar 接口测试（最简单的接口）
        payload = {
            "api_name": "trade_cal",
            "token": token,
            "params": {
                "exchange": "SSE",
                "start_date": "20260101",
                "end_date": "20260110"
            }
        }
        
        response = requests.post(
            "http://api.tushare.pro",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 检查返回结果
            if result.get("code") == 0 or "data" in result:
                print_success("Tushare API 连接成功!")
                
                # 显示积分信息（如果有）
                data = result.get("data", [])
                if data:
                    print_info(f"成功获取交易日历数据，共 {len(data)} 条记录")
                
                # 测试其他接口
                print_info("测试股票基础信息接口...")
                payload2 = {
                    "api_name": "stock_basic",
                    "token": token,
                    "params": {
                        "exchange": "",
                        "list_status": "L",
                        "limit": 5
                    }
                }
                resp2 = requests.post("http://api.tushare.pro", json=payload2, timeout=30)
                if resp2.status_code == 200 and (resp2.json().get("code") == 0 or "data" in resp2.json()):
                    print_success("股票基础信息接口可用")
                else:
                    print_warning("股票基础信息接口可能需要更高积分")
                
                return True
            else:
                error_msg = result.get("msg", "未知错误")
                if "token" in error_msg.lower() or "无效" in error_msg:
                    print_error(f"Token 无效: {error_msg}")
                    print_info("请检查 TUSHARE_TOKEN 是否正确")
                elif "积分" in error_msg or "权限" in error_msg:
                    print_warning(f"积分不足: {error_msg}")
                    print_info("签到获取积分: https://tushare.pro/user/user")
                else:
                    print_error(f"API 错误: {error_msg}")
                return False
        else:
            print_error(f"API 请求失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到 Tushare API，请检查网络")
        return False
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_moonshot():
    """测试 Kimi (月之暗面/Moonshot) API"""
    print_header("测试 Kimi (月之暗面) API")
    
    api_key = os.getenv("MOONSHOT_API_KEY", "")
    base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    enabled = os.getenv("MOONSHOT_ENABLED", "true").lower() == "true"
    
    # 检查是否启用
    if not enabled:
        print_warning("Kimi 未启用 (MOONSHOT_ENABLED=false)")
        return False
    
    # 检查 API Key
    print_info(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    print_info(f"Base URL: {base_url}")
    
    if is_placeholder(api_key, "MOONSHOT_API_KEY"):
        print_error("MOONSHOT_API_KEY 未配置或为占位符")
        print_info("获取地址: https://platform.moonshot.cn/")
        return False
    
    # 测试 API 连接
    print_info("正在测试 API 连接...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 测试 moonshot-v1-8k（基础模型）
        payload = {
            "model": "moonshot-v1-8k",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("Kimi API 连接成功!")
            print_info(f"模型: moonshot-v1-8k 可用")
            
            # 测试其他模型
            models_to_test = [
                ("moonshot-v1-32k", "32K 上下文"),
                ("moonshot-v1-128k", "128K 长上下文"),
                ("kimi-k2.5", "Kimi K2.5 最新版"),
            ]
            
            for model, desc in models_to_test:
                try:
                    payload["model"] = model
                    resp = requests.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    if resp.status_code == 200:
                        print_success(f"模型 {model} 可用 ({desc})")
                    else:
                        print_warning(f"模型 {model} 不可用: HTTP {resp.status_code}")
                except Exception as e:
                    print_warning(f"模型 {model} 测试失败: {str(e)[:50]}")
            
            return True
        elif response.status_code == 401:
            print_error("API Key 无效或已过期")
            print_info("请检查 MOONSHOT_API_KEY 是否正确")
            return False
        elif response.status_code == 429:
            print_warning("API 请求频率限制或余额不足")
            print_info("请检查账户状态: https://platform.moonshot.cn/console")
            return False
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "未知错误")
            print_error(f"请求错误: {error_msg}")
            return False
        else:
            print_error(f"API 请求失败: HTTP {response.status_code}")
            print_info(f"响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到 Kimi API，请检查网络")
        return False
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_all():
    """测试所有配置"""
    results = {}
    
    print_header("TradingAgents API 密钥测试")
    
    # 显示环境信息
    print_info(f"Python 版本: {sys.version.split()[0]}")
    print_info(f"工作目录: {os.getcwd()}")
    
    # 测试各个服务
    results["DeepSeek"] = test_deepseek()
    results["阿里百炼"] = test_dashscope()
    results["Kimi"] = test_moonshot()
    results["Tushare"] = test_tushare()
    
    # 汇总结果
    print_header("测试结果汇总")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for name, success in results.items():
        if success:
            print_success(f"{name}: 正常")
        else:
            print_error(f"{name}: 异常")
    
    print(f"\n{Colors.BOLD}总计: {success_count}/{total_count} 服务正常{Colors.RESET}")
    
    # 给出建议
    llm_available = any([results["DeepSeek"], results["阿里百炼"], results["Kimi"]])
    if success_count == 0:
        print(f"\n{Colors.RED}⚠️  没有可用的服务，请配置至少一个 LLM 提供商!{Colors.RESET}")
        print_info("推荐配置 DeepSeek (性价比高): https://platform.deepseek.com/")
        print_info("或配置 Kimi (长上下文): https://platform.moonshot.cn/")
    elif not llm_available:
        print(f"\n{Colors.YELLOW}⚠️  没有可用的 LLM 提供商，分析功能将无法使用{Colors.RESET}")
    else:
        print(f"\n{Colors.GREEN}✅ 系统配置正常，可以开始使用{Colors.RESET}")
    
    return success_count > 0


def main():
    parser = argparse.ArgumentParser(
        description="测试 TradingAgents API 密钥和模型状态",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python test_model_token.py              # 测试所有配置
    python test_model_token.py --deepseek   # 仅测试 DeepSeek
    python test_model_token.py --dashscope  # 仅测试阿里百炼
    python test_model_token.py --moonshot   # 仅测试 Kimi (月之暗面)
    python test_model_token.py --tushare    # 仅测试 Tushare
        """
    )
    
    parser.add_argument("--deepseek", action="store_true", help="仅测试 DeepSeek")
    parser.add_argument("--dashscope", action="store_true", help="仅测试阿里百炼")
    parser.add_argument("--moonshot", action="store_true", help="仅测试 Kimi (月之暗面)")
    parser.add_argument("--tushare", action="store_true", help="仅测试 Tushare")
    parser.add_argument("--env", type=str, help="指定 .env 文件路径")
    
    args = parser.parse_args()
    
    # 加载指定的 .env 文件
    if args.env:
        env_path = Path(args.env)
        if env_path.exists():
            print_info(f"加载指定环境文件: {env_path}")
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        os.environ[key.strip()] = value.strip().strip('"\'')
        else:
            print_error(f"环境文件不存在: {env_path}")
            sys.exit(1)
    else:
        load_env_file()
    
    # 根据参数选择测试项
    if args.deepseek:
        success = test_deepseek()
    elif args.dashscope:
        success = test_dashscope()
    elif args.moonshot:
        success = test_moonshot()
    elif args.tushare:
        success = test_tushare()
    else:
        success = test_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
