"""飞书链接发布器 - 主入口脚本

自动检查环境，如果缺少配置则询问用户
"""

import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from env_helper import (
    quick_env_check,
    format_env_check_message,
    get_missing_env_prompts,
    save_env_var,
)


def check_and_setup_env() -> bool:
    """
    检查环境并设置（如果需要）

    Returns:
        环境是否就绪
    """
    result = quick_env_check()

    if result["ready"]:
        return True

    # 输出检查结果
    message = format_env_check_message(result)
    if message:
        print(message)

    # 如果缺少依赖包，提示安装
    if not result["deps_ok"]:
        print("请先安装依赖包:")
        print(f"  uv pip install {' '.join(result['missing_deps'])}")
        return False

    # 如果缺少环境变量，返回 False（由 skill 调用 AskUserQuestion）
    if not result["env_ok"]:
        return False

    return True


def save_user_env_vars(env_vars: dict) -> bool:
    """
    保存用户提供的环境变量

    Args:
        env_vars: 环境变量字典 {变量名: 值}

    Returns:
        是否成功
    """
    env_file = Path.cwd() / ".env"

    for var, value in env_vars.items():
        if not save_env_var(var, value, env_file):
            return False

    return True


if __name__ == "__main__":
    # 命令行调用时执行完整检查
    from check_env import main as check_main
    sys.exit(check_main())
