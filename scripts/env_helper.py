"""环境检查辅助函数 - 用于 skill 自动检查环境"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_openclaw_config() -> Optional[Dict[str, str]]:
    """
    加载 openclaw 配置文件

    Returns:
        包含 appId 和 appSecret 的字典，如果不是 openclaw 环境则返回 None
    """
    # 检查常见的 openclaw 配置路径
    config_paths = [
        Path.home() / ".openclaw" / "config.json",
        Path.home() / ".config" / "openclaw" / "config.json",
        Path("/etc/openclaw/config.json"),
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    if "appId" in config and "appSecret" in config:
                        return {
                            "FEISHU_APP_ID": config["appId"],
                            "FEISHU_APP_SECRET": config["appSecret"],
                        }
            except (json.JSONDecodeError, KeyError):
                continue

    return None


def is_openclaw_environment() -> bool:
    """检查是否在 openclaw 环境中运行"""
    return load_openclaw_config() is not None


def load_env_file(env_path: Path) -> None:
    """加载 .env 文件"""
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ[key] = value


def find_and_load_env() -> Optional[Path]:
    """查找并加载 .env 文件，优先使用 openclaw 配置"""
    # 1. 优先检查 openclaw 配置
    openclaw_config = load_openclaw_config()
    if openclaw_config:
        for key, value in openclaw_config.items():
            os.environ[key] = value
        return None  # 表示使用了 openclaw 配置

    # 2. 否则加载 .env 文件
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent.parent.parent / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            load_env_file(env_path)
            return env_path

    return None


def check_required_env_vars() -> Tuple[bool, List[str]]:
    """
    检查必需的环境变量

    Returns:
        (是否全部存在, 缺失的变量列表)
    """
    # openclaw 环境只需要 FEISHU_BASE_URL
    if is_openclaw_environment():
        required = ["FEISHU_BASE_URL"]
    else:
        required = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_BASE_URL"]

    missing = [var for var in required if not os.getenv(var)]
    return len(missing) == 0, missing


def check_dependencies() -> Tuple[bool, List[str]]:
    """
    检查依赖包

    Returns:
        (是否全部安装, 缺失的包列表)
    """
    required = {
        "httpx": "httpx",
        "lark_oapi": "lark-oapi",
        "playwright": "playwright",
    }

    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    return len(missing) == 0, missing


def quick_env_check() -> Dict[str, any]:
    """
    快速环境检查（不输出详细信息）

    Returns:
        检查结果字典
    """
    # 加载环境变量
    env_file = find_and_load_env()

    # 检查依赖
    deps_ok, missing_deps = check_dependencies()

    # 检查环境变量
    env_ok, missing_env = check_required_env_vars()

    return {
        "env_file": env_file,
        "deps_ok": deps_ok,
        "missing_deps": missing_deps,
        "env_ok": env_ok,
        "missing_env": missing_env,
        "ready": deps_ok and env_ok,
    }


def format_env_check_message(result: Dict[str, any]) -> str:
    """格式化环境检查消息"""
    lines = []

    if not result["ready"]:
        lines.append("⚠️ 环境检查失败\n")

        if not result["deps_ok"]:
            lines.append(f"缺少依赖包: {', '.join(result['missing_deps'])}")
            lines.append(f"安装命令: uv pip install {' '.join(result['missing_deps'])}\n")

        if not result["env_ok"]:
            lines.append(f"缺少环境变量: {', '.join(result['missing_env'])}")
            lines.append("需要在 .env 文件中配置这些变量\n")

    return "\n".join(lines)


def get_missing_env_prompts() -> List[Dict[str, str]]:
    """
    获取缺失环境变量的询问提示

    Returns:
        AskUserQuestion 格式的问题列表
    """
    _, missing = check_required_env_vars()

    if not missing:
        return []

    questions = []

    # openclaw 环境只需要询问 FEISHU_BASE_URL
    if is_openclaw_environment():
        env_descriptions = {
            "FEISHU_BASE_URL": {
                "header": "飞书表格 URL",
                "question": "请提供飞书多维表格的 URL（需要设置为「互联网获得链接的人可编辑」）",
                "description": "打开飞书多维表格，点击右上角「分享」，设置权限为「互联网获得链接的人可编辑」，然后复制链接",
                "placeholder": "https://xxx.feishu.cn/base/xxxxx",
            },
        }
    else:
        env_descriptions = {
            "FEISHU_APP_ID": {
                "header": "飞书 App ID",
                "question": "请提供飞书应用的 App ID",
                "description": "在飞书开放平台创建应用后获取",
                "placeholder": "cli_xxxxxxxxxx",
            },
            "FEISHU_APP_SECRET": {
                "header": "飞书 App Secret",
                "question": "请提供飞书应用的 App Secret",
                "description": "在飞书开放平台应用凭证页面获取",
                "placeholder": "密钥字符串",
            },
            "FEISHU_BASE_URL": {
                "header": "飞书表格 URL",
                "question": "请提供飞书多维表格的 URL（需要设置为「互联网获得链接的人可编辑」）",
                "description": "打开飞书多维表格，点击右上角「分享」，设置权限为「互联网获得链接的人可编辑」，然后复制链接",
                "placeholder": "https://xxx.feishu.cn/base/xxxxx",
            },
        }

    for var in missing:
        if var in env_descriptions:
            info = env_descriptions[var]
            questions.append({
                "var": var,
                "header": info["header"],
                "question": info["question"],
                "description": info["description"],
                "placeholder": info["placeholder"],
            })

    return questions


def save_env_var(var: str, value: str, env_file: Optional[Path] = None) -> bool:
    """
    保存环境变量到 .env 文件

    Args:
        var: 变量名
        value: 变量值
        env_file: .env 文件路径（可选）

    Returns:
        是否成功
    """
    if env_file is None:
        env_file = Path.cwd() / ".env"

    try:
        # 读取现有内容
        if env_file.exists():
            with open(env_file) as f:
                lines = f.readlines()
        else:
            lines = []

        # 检查是否已存在
        var_exists = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{var}="):
                lines[i] = f"{var}={value}\n"
                var_exists = True
                break

        # 如果不存在则添加
        if not var_exists:
            # 找到飞书配置区域
            feishu_section_idx = -1
            for i, line in enumerate(lines):
                if "# 飞书" in line or "飞书" in line:
                    feishu_section_idx = i
                    break

            if feishu_section_idx >= 0:
                # 在飞书区域后添加
                lines.insert(feishu_section_idx + 1, f"{var}={value}\n")
            else:
                # 添加到末尾
                if lines and not lines[-1].endswith('\n'):
                    lines.append('\n')
                lines.append('\n# 飞书\n')
                lines.append(f"{var}={value}\n")

        # 写回文件
        with open(env_file, 'w') as f:
            f.writelines(lines)

        # 更新当前环境
        os.environ[var] = value

        return True

    except Exception as e:
        print(f"保存环境变量失败: {e}")
        return False
