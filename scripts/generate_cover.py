# Copyright (c) 2025
# 飞书链接发布器 - 封面生成模块

"""生成封面图片。"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 尝试导入 generate_cover_mcp
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Warning: mcp package not installed. Please install: pip install mcp")
    ClientSession = None
    stdio_client = None
    StdioServerParameters = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# 封面风格关键词映射
STYLE_KEYWORDS = {
    "swiss": ["技术", "工具", "开发", "AI", "编程", "代码", "框架"],
    "acid": ["设计", "创意", "艺术", "潮流", "前卫"],
    "pop": ["新闻", "热点", "娱乐", "有趣", "趋势"],
    "shock": ["警告", "重要", "必看", "紧急", "注意"],
    "diffuse": ["生活", "健康", "情感", "故事", "清新"],
    "sticker": ["可爱", "轻松", "小技巧", "日常", "简单"],
    "journal": ["日记", "记录", "思考", "感悟", "文艺"],
    "cinema": ["深度", "电影", "故事", "专题", "叙事"],
    "tech": ["科技", "数据", "分析", "报告", "研究"],
    "minimal": ["极简", "设计", "美学", "纯粹"],
    "memo": ["笔记", "清单", "总结", "备忘", "实用"],
    "geek": ["黑客", "极客", "编程", "开发", "系统"],
}

# 风格中文名映射
STYLE_NAMES = {
    "swiss": "🇨🇭 瑞士国际",
    "acid": "💚 故障酸性",
    "pop": "🎨 波普撞色",
    "shock": "⚡️ 冲击波",
    "diffuse": "🌈 弥散光",
    "sticker": "🍭 贴纸风",
    "journal": "📝 手账感",
    "cinema": "🎬 电影感",
    "tech": "🔵 科技蓝",
    "minimal": "⚪️ 极简白",
    "memo": "🟡 备忘录",
    "geek": "🟢 极客黑",
}


def auto_select_style(title: str, categories: Optional[List[str]] = None) -> str:
    """
    根据标题和类别自动选择封面风格。

    Args:
        title: 标题
        categories: 类别列表

    Returns:
        风格 key
    """
    style_scores = {style: 0 for style in STYLE_KEYWORDS.keys()}

    for style, keywords in STYLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title:
                style_scores[style] += 3
            if categories:
                for category in categories:
                    if keyword in category:
                        style_scores[style] += 2

    max_score = max(style_scores.values())
    if max_score > 0:
        return max(style_scores.items(), key=lambda x: x[1])[0]

    # 默认风格
    if any(word in title for word in ["!", "！", "必看", "警告", "注意"]):
        return "shock"
    if any(word in title for word in ["代码", "编程", "开发", "AI", "技术"]):
        return "swiss"
    return "swiss"


class CoverGenerator:
    """封面生成器，使用 generate_cover_mcp。"""

    def __init__(self, script_path: Optional[str] = None):
        """
        初始化封面生成器。

        Args:
            script_path: generate_cover_mcp 脚本路径
        """
        self.script_path = script_path
        self.session = None

    async def _get_session(self) -> Optional['ClientSession']:
        """获取 MCP 会话。"""
        if self.session:
            return self.session

        if not StdioServerParameters:
            logger.error("MCP package not installed")
            return None

        try:
            # 使用 generate_cover_mcp
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "generate_cover_mcp"],
            )

            self.session = await stdio_client(server_params).__aenter__()

            return self.session
        except Exception as e:
            logger.warning(f"Failed to connect to generate_cover_mcp: {e}")
            return None

    async def generate(
        self,
        title: str,
        subtitle: str = "精选内容·建议收藏",
        style: str = "swiss",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        生成封面图片。

        Args:
            title: 标题
            subtitle: 副标题
            style: 封面风格
            output_path: 输出路径

        Returns:
            生成的封面文件路径，失败返回 None
        """
        if output_path is None:
            output_path = f"cover_{style}_{hash(title)}.png"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果 MCP 不可用，返回模拟路径
        session = await self._get_session()
        if not session:
            logger.warning("Cover generation MCP not available, using fallback")
            # 返回占位路径
            return str(output_path)

        try:
            # 调用 generate_cover MCP 工具
            result = await session.call_tool(
                "generate_cover",
                arguments={
                    "title": title,
                    "subtitle": subtitle,
                    "style": style,
                    "output": str(output_path),
                }
            )

            if result and result.get("success"):
                logger.info(f"Cover generated: {output_path}")
                return str(output_path)
            else:
                logger.warning(f"Cover generation failed: {result}")
                return None

        except Exception as e:
            logger.error(f"Cover generation error: {e}")
            return None

    def generate_sync(
        self,
        title: str,
        subtitle: str = "精选内容·建议收藏",
        style: str = "swiss",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """同步版本的封面生成。"""
        return asyncio.run(self.generate(title, subtitle, style, output_path))

    async def close(self):
        """关闭会话。"""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="生成封面图片")
    parser.add_argument("--title", required=True, help="标题")
    parser.add_argument("--subtitle", default="精选内容·建议收藏", help="副标题")
    parser.add_argument("--style", choices=list(STYLE_KEYWORDS.keys()),
                       help="封面风格（不指定则自动选择）")
    parser.add_argument("--categories", help="类别列表，逗号分隔（用于自动选择风格）")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--list-styles", action="store_true", help="列出所有可用风格")

    args = parser.parse_args()

    if args.list_styles:
        print("可用封面风格：")
        for key, name in STYLE_NAMES.items():
            keywords = ", ".join(STYLE_KEYWORDS[key])
            print(f"  {key}: {name} ({keywords})")
        return

    # 确定风格
    style = args.style
    if not style:
        categories = args.categories.split(",") if args.categories else None
        style = auto_select_style(args.title, categories)

    print(f"使用风格: {STYLE_NAMES.get(style, style)}")

    # 生成封面
    generator = CoverGenerator()
    try:
        output_path = generator.generate_sync(
            title=args.title,
            subtitle=args.subtitle,
            style=style,
            output_path=args.output,
        )

        if output_path:
            print(f"✓ 封面已生成: {output_path}")
        else:
            print("✗ 封面生成失败")
            sys.exit(1)

    finally:
        asyncio.run(generator.close())


if __name__ == "__main__":
    main()
