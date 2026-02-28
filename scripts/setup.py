# Copyright (c) 2025
# 飞书链接发布器 - 环境检查与安装

"""检查环境并自动安装依赖。"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class EnvChecker:
    """环境检查器。"""

    # 所需的 Python 包
    REQUIRED_PACKAGES = {
        "httpx": "httpx>=0.27.0",
        "lark-oapi": "lark-oapi>=2.0.0",
    }

    # 可选的 Python 包
    OPTIONAL_PACKAGES = {
        "mcp": "mcp>=0.1.0",
        "json_repair": "json-repair>=0.25.0",
    }

    # 所需的环境变量
    REQUIRED_ENV_VARS = [
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_BASE_URL",
    ]

    def __init__(self, use_uv: bool = True):
        """
        初始化环境检查器。

        Args:
            use_uv: 是否使用 uv 进行包管理
        """
        self.use_uv = use_uv
        self.skill_dir = Path(__file__).parent.parent
        self.venv_dir = self.skill_dir / ".venv"
        self.env_file = self.skill_dir / ".env"

    def check_python_version(self) -> Tuple[bool, str]:
        """检查 Python 版本。"""
        version = sys.version_info
        if version >= (3, 10):
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python {version.major}.{version.minor}.{version.micro} (需要 3.10+)"

    def check_command(self, command: str) -> bool:
        """检查命令是否可用。"""
        try:
            subprocess.run(
                [command, "--version"],
                capture_output=True,
                check=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def check_uv(self) -> Tuple[bool, str]:
        """检查 uv 是否安装。"""
        if self.check_command("uv"):
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version = result.stdout.strip()
            return True, f"uv {version}"
        return False, "uv 未安装"

    def check_packages(self) -> Tuple[List[str], List[str]]:
        """
        检查已安装的包。

        Returns:
            (已安装列表, 缺失列表)
        """
        installed = []
        missing = []

        for package, _ in self.REQUIRED_PACKAGES.items():
            try:
                __import__(package.replace("-", "_"))
                installed.append(package)
            except ImportError:
                missing.append(package)

        return installed, missing

    def check_optional_packages(self) -> List[str]:
        """检查可选包的安装状态。"""
        available = []
        for package, _ in self.OPTIONAL_PACKAGES.items():
            try:
                __import__(package.replace("-", "_"))
                available.append(package)
            except ImportError:
                pass
        return available

    def check_env_vars(self) -> Tuple[List[str], List[str]]:
        """
        检查环境变量。

        Returns:
            (已设置列表, 缺失列表)
        """
        set_vars = []
        missing_vars = []

        for var in self.REQUIRED_ENV_VARS:
            if os.getenv(var):
                set_vars.append(var)
            else:
                missing_vars.append(var)

        return set_vars, missing_vars

    def create_venv(self) -> bool:
        """创建虚拟环境。"""
        if self.venv_dir.exists():
            logger.info(f"虚拟环境已存在: {self.venv_dir}")
            return True

        logger.info(f"创建虚拟环境: {self.venv_dir}")

        if self.use_uv:
            try:
                subprocess.run(
                    ["uv", "venv", str(self.venv_dir)],
                    check=True,
                    cwd=self.skill_dir,
                )
                logger.info("✓ 虚拟环境创建成功")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"✗ 虚拟环境创建失败: {e}")
                return False
        else:
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_dir)],
                    check=True,
                    cwd=self.skill_dir,
                )
                logger.info("✓ 虚拟环境创建成功")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"✗ 虚拟环境创建失败: {e}")
                return False

    def install_packages(self, packages: List[str]) -> bool:
        """安装包。"""
        if not packages:
            return True

        logger.info(f"安装包: {', '.join(packages)}")

        if self.use_uv:
            try:
                # 检查是否在虚拟环境中
                venv_python = self.venv_dir / "bin" / "python"
                if sys.platform == "win32":
                    venv_python = self.venv_dir / "Scripts" / "python.exe"

                cmd = [
                    "uv", "pip", "install",
                    "--python", str(venv_python),
                ] + packages

                subprocess.run(cmd, check=True, cwd=self.skill_dir)
                logger.info("✓ 包安装成功")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"✗ 包安装失败: {e}")
                return False
        else:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + packages,
                    check=True,
                )
                logger.info("✓ 包安装成功")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"✗ 包安装失败: {e}")
                return False

    def install_uv(self) -> bool:
        """安装 uv。"""
        logger.info("安装 uv...")

        try:
            # 使用官方安装脚本
            subprocess.run(
                ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"],
                shell=True,
                check=True,
            )
            logger.info("✓ uv 安装成功")
            return True
        except subprocess.CalledProcessError:
            logger.error("✗ uv 安装失败")
            return False

    def create_env_file(self) -> bool:
        """创建 .env 文件模板。"""
        if self.env_file.exists():
            logger.info(".env 文件已存在")
            return True

        example_file = self.skill_dir / "assets" / ".env.example"
        if not example_file.exists():
            logger.warning(".env.example 不存在")
            return False

        import shutil
        shutil.copy(example_file, self.env_file)
        logger.info(f"✓ 已创建 .env 文件模板，请填写配置: {self.env_file}")
        return True

    def setup(self, auto_install: bool = False) -> bool:
        """
        执行完整的环境检查和设置。

        Args:
            auto_install: 自动安装缺失的组件

        Returns:
            环境是否就绪
        """
        logger.info("=" * 60)
        logger.info("飞书链接发布器 - 环境检查")
        logger.info("=" * 60)

        all_ok = True

        # 1. Python 版本
        logger.info("\n[1/6] 检查 Python 版本")
        python_ok, python_info = self.check_python_version()
        if python_ok:
            logger.info(f"✓ {python_info}")
        else:
            logger.error(f"✗ {python_info}")
            all_ok = False

        # 2. uv 检查
        logger.info("\n[2/6] 检查 uv")
        if self.use_uv:
            uv_ok, uv_info = self.check_uv()
            if uv_ok:
                logger.info(f"✓ {uv_info}")
            else:
                logger.warning(f"✗ {uv_info}")
                if auto_install:
                    logger.info("尝试安装 uv...")
                    if not self.install_uv():
                        logger.info("切换到 pip 模式")
                        self.use_uv = False
                else:
                    logger.info("提示: 运行 'pip install uv' 或使用 --install 安装")
                    self.use_uv = False

        # 3. 虚拟环境
        logger.info("\n[3/6] 检查虚拟环境")
        if not self.venv_dir.exists():
            logger.warning("虚拟环境不存在")
            if auto_install:
                if not self.create_venv():
                    all_ok = False
            else:
                logger.info("提示: 使用 --install 创建虚拟环境")
        else:
            logger.info(f"✓ 虚拟环境: {self.venv_dir}")

        # 4. Python 包
        logger.info("\n[4/6] 检查 Python 包")
        installed, missing = self.check_packages()
        if installed:
            logger.info(f"✓ 已安装: {', '.join(installed)}")
        if missing:
            logger.warning(f"✗ 缺失: {', '.join(missing)}")
            if auto_install:
                packages = [self.REQUIRED_PACKAGES[p] for p in missing]
                if not self.install_packages(packages):
                    all_ok = False
            else:
                logger.info("提示: 使用 --install 安装缺失的包")

        # 可选包
        optional = self.check_optional_packages()
        if optional:
            logger.info(f"  (可选) 已安装: {', '.join(optional)}")
        else:
            missing_optional = [p for p in self.OPTIONAL_PACKAGES if p not in optional]
            if missing_optional:
                logger.info(f"  (可选) 未安装: {', '.join(missing_optional)}")

        # 5. 环境变量
        logger.info("\n[5/6] 检查环境变量")
        set_vars, missing_vars = self.check_env_vars()
        if set_vars:
            logger.info(f"✓ 已设置: {', '.join(set_vars)}")
        if missing_vars:
            logger.warning(f"✗ 缺失: {', '.join(missing_vars)}")
            all_ok = False
            if not self.env_file.exists():
                self.create_env_file()

        # 6. 总结
        logger.info("\n[6/6] 检查完成")
        logger.info("=" * 60)

        if all_ok:
            logger.info("✓ 环境就绪，可以开始使用")
        else:
            logger.warning("✗ 环境未完全就绪")
            logger.info("提示: 运行 'python -m scripts.setup --install' 自动安装缺失组件")

        return all_ok


def main():
    import argparse

    parser = argparse.ArgumentParser(description="环境检查与设置")
    parser.add_argument("--install", action="store_true", help="自动安装缺失的组件")
    parser.add_argument("--no-uv", action="store_true", help="不使用 uv，改用 pip")
    parser.add_argument("--check-only", action="store_true", help="只检查不修改")

    args = parser.parse_args()

    checker = EnvChecker(use_uv=not args.no_uv)

    if args.check_only:
        # 只检查，不安装
        checker.setup(auto_install=False)
    elif args.install:
        # 自动安装
        checker.setup(auto_install=True)
    else:
        # 默认检查
        ok = checker.setup(auto_install=False)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
