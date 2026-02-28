#!/usr/bin/env python3
"""环境检查脚本 - 检查所有必要的配置和权限"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_env_file(env_path: Path) -> None:
    """加载 .env 文件"""
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # 支持 KEY=value 和 KEY = value 格式
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ[key] = value

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_python_version() -> bool:
    """检查 Python 版本"""
    version = sys.version_info
    print(f"\n{BLUE}[1/7] 检查 Python 版本{RESET}")

    if version >= (3, 10):
        print(f"  {GREEN}✓{RESET} Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  {RED}✗{RESET} Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print(f"  {YELLOW}需要 Python 3.10+{RESET}")
        return False


def check_dependencies() -> Tuple[bool, List[str]]:
    """检查依赖包"""
    print(f"\n{BLUE}[2/7] 检查依赖包{RESET}")

    required = {
        "httpx": "HTTP 客户端",
        "lark_oapi": "飞书 SDK",
        "playwright": "浏览器自动化（封面生成）",
        "mcp": "MCP 客户端",
    }

    missing = []
    for package, desc in required.items():
        try:
            __import__(package)
            print(f"  {GREEN}✓{RESET} {package} ({desc})")
        except ImportError:
            print(f"  {RED}✗{RESET} {package} ({desc}) - 未安装")
            missing.append(package)

    return len(missing) == 0, missing


def check_env_vars() -> Tuple[bool, List[str]]:
    """检查环境变量（不显示值）"""
    print(f"\n{BLUE}[3/7] 检查环境变量{RESET}")

    required = {
        "FEISHU_APP_ID": "飞书应用 ID",
        "FEISHU_APP_SECRET": "飞书应用密钥",
        "FEISHU_BASE_URL": "飞书多维表格 URL",
    }

    optional = {
        "JINA_API_KEY": "Jina API 密钥（可选）",
    }

    missing = []

    # 检查必需的环境变量
    for var, desc in required.items():
        value = os.getenv(var)
        if value and value.strip():
            # 显示部分值（前3后3字符）
            masked = f"{value[:3]}...{value[-3:]}" if len(value) > 6 else "***"
            print(f"  {GREEN}✓{RESET} {var} = {masked}")
        else:
            print(f"  {RED}✗{RESET} {var} - 未设置")
            missing.append(var)

    # 检查可选的环境变量
    for var, desc in optional.items():
        value = os.getenv(var)
        if value and value.strip():
            masked = f"{value[:3]}...{value[-3:]}" if len(value) > 6 else "***"
            print(f"  {GREEN}✓{RESET} {var} = {masked} ({desc})")
        else:
            print(f"  {YELLOW}○{RESET} {var} - 未设置 ({desc})")

    return len(missing) == 0, missing


def check_playwright_browsers() -> bool:
    """检查 Playwright 浏览器"""
    print(f"\n{BLUE}[4/7] 检查 Playwright 浏览器{RESET}")

    try:
        import playwright
        from pathlib import Path

        # 检查 chromium 是否已安装
        cache_dir = Path.home() / "Library/Caches/ms-playwright"
        chromium_dirs = list(cache_dir.glob("chromium*"))

        if chromium_dirs:
            print(f"  {GREEN}✓{RESET} Chromium 已安装")
            return True
        else:
            print(f"  {RED}✗{RESET} Chromium 未安装")
            print(f"  {YELLOW}运行: uv run playwright install chromium{RESET}")
            return False
    except ImportError:
        print(f"  {YELLOW}○{RESET} Playwright 未安装，跳过检查")
        return True


def check_feishu_connection() -> bool:
    """检查飞书连接"""
    print(f"\n{BLUE}[5/7] 检查飞书连接{RESET}")

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    base_url = os.getenv("FEISHU_BASE_URL")

    if not all([app_id, app_secret, base_url]):
        print(f"  {YELLOW}○{RESET} 跳过（环境变量未配置）")
        return True

    try:
        import lark_oapi as lark

        client = lark.Client.builder().app_id(app_id).app_secret(app_secret).build()

        # 测试获取 tenant_access_token
        from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest

        request = InternalTenantAccessTokenRequest.builder().build()
        response = client.auth.v3.tenant_access_token.internal(request)

        if response.success():
            print(f"  {GREEN}✓{RESET} 飞书 API 连接成功")
            return True
        else:
            print(f"  {RED}✗{RESET} 飞书 API 连接失败")
            print(f"  {YELLOW}错误: {response.msg}{RESET}")
            return False

    except Exception as e:
        print(f"  {RED}✗{RESET} 连接失败: {str(e)}")
        return False


def check_feishu_base_fields() -> Tuple[bool, List[str]]:
    """检查飞书多维表格字段"""
    print(f"\n{BLUE}[6/7] 检查飞书多维表格字段{RESET}")

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    base_url = os.getenv("FEISHU_BASE_URL")

    if not all([app_id, app_secret, base_url]):
        print(f"  {YELLOW}○{RESET} 跳过（环境变量未配置）")
        return True, []

    try:
        import lark_oapi as lark
        from lark_oapi.api.bitable.v1 import ListAppTableFieldRequest
        from urllib.parse import urlparse

        # 解析 app_token
        parsed = urlparse(base_url)
        path_parts = parsed.path.strip("/").split("/")
        app_token = path_parts[path_parts.index("base") + 1]

        client = lark.Client.builder().app_id(app_id).app_secret(app_secret).build()

        # 获取第一个表的 table_id
        from lark_oapi.api.bitable.v1 import ListAppTableRequest

        list_req = ListAppTableRequest.builder().app_token(app_token).build()
        list_resp = client.bitable.v1.app_table.list(list_req)

        if not list_resp.success() or not list_resp.data.items:
            print(f"  {RED}✗{RESET} 无法获取数据表")
            return False, []

        table_id = list_resp.data.items[0].table_id

        # 获取字段列表
        request = ListAppTableFieldRequest.builder().app_token(app_token).table_id(table_id).build()
        response = client.bitable.v1.app_table_field.list(request)

        if not response.success():
            print(f"  {RED}✗{RESET} 无法获取字段列表")
            return False, []

        # 期望的字段
        expected_fields = {
            "标题": "超链接",
            "简介": "文本",
            "类型": "多选",
            "分享者": "文本",
            "创建日期": "日期",
            "封面": "附件",
        }

        # 检查字段
        actual_fields = {item.field_name: item.type for item in response.data.items}
        missing = []

        for field_name, field_type in expected_fields.items():
            if field_name in actual_fields:
                actual_type = str(actual_fields[field_name])
                print(f"  {GREEN}✓{RESET} {field_name} ({actual_type})")
            else:
                print(f"  {RED}✗{RESET} {field_name} - 字段不存在")
                missing.append(field_name)

        return len(missing) == 0, missing

    except Exception as e:
        print(f"  {RED}✗{RESET} 检查失败: {str(e)}")
        return False, []


def check_feishu_permissions() -> Tuple[bool, List[str]]:
    """检查飞书应用权限"""
    print(f"\n{BLUE}[7/7] 检查飞书应用权限{RESET}")

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not all([app_id, app_secret]):
        print(f"  {YELLOW}○{RESET} 跳过（环境变量未配置）")
        return True, []

    required_permissions = [
        "bitable:app",  # 多维表格读写
        "drive:drive",  # 云文档读写（上传封面）
    ]

    print(f"  {YELLOW}需要以下权限:{RESET}")
    for perm in required_permissions:
        print(f"    - {perm}")

    print(f"\n  {YELLOW}请在飞书开放平台确认已开启以上权限{RESET}")
    print(f"  {BLUE}https://open.feishu.cn/app{RESET}")

    return True, []


def main():
    """主函数"""
    # 加载 .env 文件
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent.parent.parent / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            load_env_file(env_path)
            break

    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}飞书链接发布器 - 环境检查{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    results = []

    # 1. Python 版本
    results.append(("Python 版本", check_python_version()))

    # 2. 依赖包
    deps_ok, missing_deps = check_dependencies()
    results.append(("依赖包", deps_ok))

    # 3. 环境变量
    env_ok, missing_env = check_env_vars()
    results.append(("环境变量", env_ok))

    # 4. Playwright 浏览器
    results.append(("Playwright", check_playwright_browsers()))

    # 5. 飞书连接
    results.append(("飞书连接", check_feishu_connection()))

    # 6. 飞书字段
    fields_ok, missing_fields = check_feishu_base_fields()
    results.append(("飞书字段", fields_ok))

    # 7. 飞书权限
    perms_ok, _ = check_feishu_permissions()
    results.append(("飞书权限", perms_ok))

    # 总结
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}检查结果{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    all_passed = all(result[1] for result in results)

    for name, passed in results:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {name}")

    # 修复建议
    if not all_passed:
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}修复建议{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}\n")

        if missing_deps:
            print(f"{YELLOW}安装缺失的依赖包:{RESET}")
            print(f"  uv pip install {' '.join(missing_deps)}")
            print()

        if missing_env:
            print(f"{YELLOW}配置缺失的环境变量:{RESET}")
            print(f"  在项目根目录的 .env 文件中添加:")
            for var in missing_env:
                if var == "FEISHU_APP_ID":
                    print(f"    {var}=your_app_id")
                elif var == "FEISHU_APP_SECRET":
                    print(f"    {var}=your_app_secret")
                elif var == "FEISHU_BASE_URL":
                    print(f"    {var}=https://xxx.feishu.cn/base/app_token")
            print()

        if missing_fields:
            print(f"{YELLOW}在飞书多维表格中添加缺失的字段:{RESET}")
            for field in missing_fields:
                print(f"    - {field}")
            print()

    print()
    if all_passed:
        print(f"{GREEN}✓ 所有检查通过！环境配置正确。{RESET}\n")
        return 0
    else:
        print(f"{RED}✗ 部分检查未通过，请根据上述建议修复。{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
