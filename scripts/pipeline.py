# Copyright (c) 2025
# 飞书链接发布器 - 完整流程脚本

"""完整的链接处理流程：抓取 -> 分析 -> 封面 -> 发布"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from fetch_content import ContentFetcher
from generate_cover import CoverGenerator, auto_select_style
from publish_feishu import FeishuPublisher

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class LinkProcessor:
    """链接处理器 - 完整流程。"""

    def __init__(
        self,
        feishu_app_id: Optional[str] = None,
        feishu_app_secret: Optional[str] = None,
        feishu_base_url: Optional[str] = None,
    ):
        """初始化处理器。"""
        self.fetcher = ContentFetcher()
        self.cover_generator = CoverGenerator()
        self.publisher = FeishuPublisher(feishu_app_id, feishu_app_secret, feishu_base_url)

    def analyze_content(self, url: str, content: str, fetch_result: dict) -> dict:
        """
        分析内容，生成标题、摘要、类别等。

        注意：这个方法由 LLM 直接调用，不需要单独的 LLM 客户端。
        返回的结果由 Claude（使用本技能的模型）生成。

        Args:
            url: 原始链接
            content: 抓取的内容
            fetch_result: 抓取结果元数据

        Returns:
            分析结果字典
        """
        # 这个方法作为占位符，实际分析由 Claude 完成
        # Claude 会根据 SKILL.md 中的指令生成分析结果
        return {
            "url": url,
            "title": "",
            "summary": "",
            "categories": [],
            "score": 0,
            "cover_style": "swiss",
        }

    def process(
        self,
        url: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        categories: Optional[List[str]] = None,
        cover_style: Optional[str] = None,
        sender: Optional[str] = None,
        generate_cover: bool = True,
        publish: bool = True,
        output_dir: Optional[str] = None,
    ) -> dict:
        """
        处理单个链接的完整流程。

        Args:
            url: 目标链接
            title: 标题（不提供则自动生成）
            summary: 摘要（不提供则自动生成）
            categories: 类别（不提供则自动识别）
            cover_style: 封面风格（不提供则自动选择）
            sender: 分享者
            generate_cover: 是否生成封面
            publish: 是否发布到飞书
            output_dir: 输出目录

        Returns:
            处理结果字典
        """
        result = {
            "url": url,
            "success": False,
            "steps": {},
        }

        output_path = Path(output_dir) if output_dir else Path.cwd() / "output"
        output_path.mkdir(parents=True, exist_ok=True)

        # 步骤 1: 抓取内容
        logger.info(f"[步骤 1/4] 抓取内容: {url}")
        try:
            fetch_result = self.fetcher.auto_fetch(url)
            result["steps"]["fetch"] = {"success": True, "data": fetch_result}
            logger.info(f"✓ 内容抓取完成，类型: {fetch_result.get('type')}")
        except Exception as e:
            logger.error(f"✗ 内容抓取失败: {e}")
            result["steps"]["fetch"] = {"success": False, "error": str(e)}
            return result

        # 步骤 2: 分析内容（由调用者/LLM 完成）
        logger.info("[步骤 2/4] 分析内容")
        # 注意：实际分析由 Claude 完成，这里只是记录
        result["steps"]["analyze"] = {"success": True}

        # 如果提供了分析结果，使用它们
        if title:
            result["title"] = title
        if summary:
            result["summary"] = summary
        if categories:
            result["categories"] = categories

        # 默认值
        result.setdefault("title", fetch_result.get("title", url[:50]))
        result.setdefault("summary", fetch_result.get("content", "")[:200] + "...")
        result.setdefault("categories", ["其他"])

        # 步骤 3: 生成封面
        cover_path = None
        if generate_cover:
            logger.info("[步骤 3/4] 生成封面")
            try:
                # 自动选择风格
                if not cover_style:
                    cover_style = auto_select_style(
                        result["title"],
                        result.get("categories")
                    )

                cover_filename = f"cover_{cover_style}_{abs(hash(url)) % 1000000}.png"
                cover_file = output_path / cover_filename

                # 生成封面
                cover_path = self.cover_generator.generate_sync(
                    title=result["title"],
                    subtitle="精选内容·建议收藏",
                    style=cover_style,
                    output_path=str(cover_file),
                )

                if cover_path:
                    result["cover_path"] = cover_path
                    result["cover_style"] = cover_style
                    logger.info(f"✓ 封面已生成: {cover_path}")
                else:
                    logger.warning("封面生成失败，跳过")
                    result["steps"]["cover"] = {"success": False, "error": "Generation failed"}

            except Exception as e:
                logger.warning(f"封面生成失败: {e}")
                result["steps"]["cover"] = {"success": False, "error": str(e)}

        # 步骤 4: 发布到飞书
        if publish:
            logger.info("[步骤 4/4] 发布到飞书")
            try:
                success = self.publisher.publish(
                    title=result["title"],
                    url=url,
                    summary=result.get("summary", ""),
                    categories=result.get("categories", []),
                    cover_path=cover_path,
                    sender=sender,
                    created_at=int(datetime.now().timestamp() * 1000),
                )
                result["steps"]["publish"] = {"success": success}
                result["success"] = success
                if success:
                    logger.info("✓ 发布成功")
                else:
                    logger.warning("发布失败")
            except Exception as e:
                logger.error(f"发布失败: {e}")
                result["steps"]["publish"] = {"success": False, "error": str(e)}
        else:
            result["success"] = True
            logger.info("发布已跳过")

        return result

    def process_batch(
        self,
        urls: List[str],
        analyses: Optional[List[dict]] = None,
        sender: Optional[str] = None,
        generate_cover: bool = True,
        publish: bool = True,
        output_dir: Optional[str] = None,
    ) -> List[dict]:
        """
        批量处理链接。

        Args:
            urls: 链接列表
            analyses: 预先提供的分析结果列表
            sender: 分享者
            generate_cover: 是否生成封面
            publish: 是否发布
            output_dir: 输出目录

        Returns:
            处理结果列表
        """
        results = []

        for idx, url in enumerate(urls, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"处理链接 [{idx}/{len(urls)}]: {url}")
            logger.info(f"{'='*60}")

            # 获取对应的分析结果
            analysis = analyses[idx - 1] if analyses else None

            result = self.process(
                url=url,
                title=analysis.get("title") if analysis else None,
                summary=analysis.get("summary") if analysis else None,
                categories=analysis.get("categories") if analysis else None,
                cover_style=analysis.get("cover_style") if analysis else None,
                sender=sender,
                generate_cover=generate_cover,
                publish=publish,
                output_dir=output_dir,
            )

            results.append(result)

        # 汇总
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"\n{'='*60}")
        logger.info(f"批量处理完成: {success_count}/{len(urls)} 成功")
        logger.info(f"{'='*60}")

        return results

    def close(self):
        """关闭资源。"""
        self.fetcher.close()
        asyncio.run(self.cover_generator.close())


def main():
    parser = argparse.ArgumentParser(description="飞书链接发布器 - 完整流程")
    parser.add_argument("--url", help="单个链接")
    parser.add_argument("--urls", help="多个链接，逗号分隔")
    parser.add_argument("--url-file", help="从文件读取链接列表")
    parser.add_argument("--json-file", help="从 JSON 文件读取分析结果")

    # 分析结果（可选）
    parser.add_argument("--title", help="标题")
    parser.add_argument("--summary", help="摘要")
    parser.add_argument("--categories", help="类别，逗号分隔")
    parser.add_argument("--cover-style", help="封面风格")
    parser.add_argument("--sender", help="分享者")

    # 选项
    parser.add_argument("--no-cover", action="store_true", help="不生成封面")
    parser.add_argument("--no-publish", action="store_true", help="不发布到飞书")
    parser.add_argument("--output-dir", "-o", help="输出目录")
    parser.add_argument("--dry-run", action="store_true", help="只测试不发布")

    args = parser.parse_args()

    # 收集 URL 列表
    urls = []
    if args.url:
        urls.append(args.url)
    if args.urls:
        urls.extend([u.strip() for u in args.urls.split(",")])
    if args.url_file:
        urls.extend(Path(args.url_file).read_text(encoding="utf-8").strip().split("\n"))

    if not urls:
        logger.error("请提供至少一个 URL (--url, --urls, 或 --url-file)")
        sys.exit(1)

    # 解析类别
    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # 读取 JSON 分析结果
    analyses = None
    if args.json_file:
        analyses = json.loads(Path(args.json_file).read_text(encoding="utf-8"))

    # 创建处理器
    processor = LinkProcessor()

    try:
        if len(urls) == 1:
            # 单个链接处理
            result = processor.process(
                url=urls[0],
                title=args.title,
                summary=args.summary,
                categories=categories,
                cover_style=args.cover_style,
                sender=args.sender,
                generate_cover=not args.no_cover,
                publish=not args.no_publish and not args.dry_run,
                output_dir=args.output_dir,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # 批量处理
            results = processor.process_batch(
                urls=urls,
                analyses=analyses,
                sender=args.sender,
                generate_cover=not args.no_cover,
                publish=not args.no_publish and not args.dry_run,
                output_dir=args.output_dir,
            )

            # 保存结果
            output_file = Path(args.output_dir) / "results.json" if args.output_dir else Path("results.json")
            output_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))
            logger.info(f"结果已保存到: {output_file}")

    finally:
        processor.close()


if __name__ == "__main__":
    main()
