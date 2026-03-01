# Copyright (c) 2025
# 飞书链接发布器 - 内容抓取模块

"""抓取网页内容，支持微信公众号文章和普通网页。"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ContentFetcher:
    """网页内容抓取器。"""

    def __init__(self, jina_api_key: Optional[str] = None):
        """
        初始化抓取器。

        Args:
            jina_api_key: Jina API Key，可选。不提供则使用 r.jina.ai 前缀方式
        """
        self.jina_api_key = jina_api_key
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)

    def fetch_with_jina(self, url: str) -> str:
        """
        使用 Jina Reader API 抓取网页内容。

        Args:
            url: 目标 URL

        Returns:
            Markdown 格式的网页内容
        """
        # 使用 r.jina.ai 前缀方式（不需要 API Key）
        jina_url = f"https://r.jina.ai/{url}"

        logger.info(f"Fetching content from: {jina_url}")

        try:
            response = self.client.get(jina_url)
            response.raise_for_status()
            content = response.text

            logger.info(f"Fetched {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"Failed to fetch content: {e}")
            return ""

    def fetch_wechat_article(self, url: str) -> dict:
        """
        抓取微信公众号文章。

        Args:
            url: 微信文章 URL

        Returns:
            包含 title, content, author 等字段的字典
        """
        logger.info(f"Fetching WeChat article: {url}")

        # 微信文章通常需要专用 MCP 或特殊处理
        # Jina Reader 对微信文章支持不佳，容易超时
        logger.warning("微信文章获取失败 - Jina Reader 对微信文章支持有限")
        logger.warning("建议：使用微信文章专用 MCP 或手动复制内容")

        return {
            "url": url,
            "title": "微信文章（需要专用工具）",
            "content": f"⚠️ 微信公众号文章需要专用工具处理\n\n链接: {url}\n\n建议：\n1. 使用微信文章专用 MCP\n2. 或手动复制文章内容",
            "error": "wechat_not_supported",
        }

    def fetch_github_repo(self, url: str) -> dict:
        """
        抓取 GitHub 仓库信息。

        Args:
            url: GitHub 仓库 URL

        Returns:
            包含仓库信息的字典
        """
        logger.info(f"Fetching GitHub repo: {url}")

        # 使用 Jina Reader API
        content = self.fetch_with_jina(url)

        # 从 URL 提取仓库信息
        pattern = r"github\.com/([^/]+)/([^/]+)"
        match = re.search(pattern, url)
        owner = repo = ""
        if match:
            owner = match.group(1)
            repo = match.group(2).replace(".git", "")

        return {
            "url": url,
            "owner": owner,
            "repo": repo,
            "content": content,
        }

    def auto_fetch(self, url: str) -> dict:
        """
        自动识别链接类型并抓取内容。

        Args:
            url: 目标 URL

        Returns:
            包含内容和元数据的字典
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        result = {"url": url, "type": "unknown", "content": ""}

        if "mp.weixin.qq.com" in url or "weixin.qq.com" in url:
            result["type"] = "wechat"
            article = self.fetch_wechat_article(url)
            result.update(article)
        elif "github.com" in domain or "gitlab.com" in domain:
            result["type"] = "repo"
            repo_info = self.fetch_github_repo(url)
            result.update(repo_info)
        else:
            result["type"] = "webpage"
            result["content"] = self.fetch_with_jina(url)

        return result

    def close(self):
        """关闭 HTTP 客户端。"""
        self.client.close()


def main():
    parser = argparse.ArgumentParser(description="抓取网页内容")
    parser.add_argument("--url", required=True, help="目标 URL")
    parser.add_argument("--type", choices=["auto", "wechat", "github", "webpage"],
                       default="auto", help="链接类型，默认自动识别")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径")
    parser.add_argument("--jina-api-key", help="Jina API Key（可选）")

    args = parser.parse_args()

    fetcher = ContentFetcher(jina_api_key=args.jina_api_key)

    try:
        if args.type == "auto":
            result = fetcher.auto_fetch(args.url)
        elif args.type == "wechat":
            result = fetcher.fetch_wechat_article(args.url)
        elif args.type == "github":
            result = fetcher.fetch_github_repo(args.url)
        else:
            result = {
                "url": args.url,
                "type": "webpage",
                "content": fetcher.fetch_with_jina(args.url)
            }

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            logger.info(f"Result saved to: {args.output}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    finally:
        fetcher.close()


if __name__ == "__main__":
    main()
