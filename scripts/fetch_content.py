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

# 尝试导入 MCP 服务器功能
try:
    from miroflow_tools.mcp_servers.wechat_article_mcp_server import WeChatArticleFetcher
    WECHAT_MCP_AVAILABLE = True
except ImportError:
    WECHAT_MCP_AVAILABLE = False
    logger.debug("WeChat MCP server not available")

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    logger.debug("Web scraping dependencies not available")


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
        # 如果有 API Key，使用官方 API
        if self.jina_api_key:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {"Authorization": f"Bearer {self.jina_api_key}"}
            logger.info(f"Using Jina Reader with API key: {jina_url}")
        else:
            # 兜底：使用 r.jina.ai 前缀方式（不需要 API Key）
            jina_url = f"https://r.jina.ai/{url}"
            headers = {}
            logger.info(f"Using r.jina.ai (fallback): {jina_url}")

        try:
            response = self.client.get(jina_url, headers=headers)
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

        # 优先使用 WeChat MCP 服务器
        if WECHAT_MCP_AVAILABLE:
            try:
                fetcher = WeChatArticleFetcher()
                result = fetcher.get_an_article(url)

                if result["content_flag"] == 1:
                    article_info = fetcher.format_content(result["content"])
                    logger.info(f"✓ 使用 WeChat MCP 成功获取: {article_info['article_title']}")
                    return {
                        "url": url,
                        "title": article_info["article_title"],
                        "author": article_info["author"],
                        "content": "\n".join(article_info["format_texts"]),
                        "nickname": article_info["nickname"],
                        "createTime": article_info["createTime"],
                    }
                else:
                    logger.warning(f"WeChat MCP 获取失败: {result.get('error', 'Unknown')}")
            except Exception as e:
                logger.warning(f"WeChat MCP 异常: {e}")

        # 如果有 Jina API Key，尝试使用
        if self.jina_api_key:
            logger.info("尝试使用 Jina Reader (with API key)")
            content = self.fetch_with_jina(url)
            if content:
                return {"url": url, "title": "微信文章", "content": content}

        # 兜底：使用 r.jina.ai
        logger.info("使用 r.jina.ai 作为兜底方案")
        content = self.fetch_with_jina(url)
        if content:
            return {"url": url, "title": "微信文章", "content": content}

        # 完全失败
        return {
            "url": url,
            "title": "微信文章（获取失败）",
            "content": f"⚠️ 无法获取微信文章内容\n\n链接: {url}",
            "error": "fetch_failed",
        }

    def fetch_webpage(self, url: str) -> str:
        """
        抓取普通网页内容。

        Args:
            url: 网页 URL

        Returns:
            网页内容（Markdown 或文本格式）
        """
        logger.info(f"Fetching webpage: {url}")

        # 优先使用 Web Scraping MCP
        if WEB_SCRAPING_AVAILABLE:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # 移除脚本和样式
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()

                # 提取主要内容
                main_content = (
                    soup.find("main") or
                    soup.find("article") or
                    soup.find("div", class_=re.compile(r"content|main|article", re.I)) or
                    soup.body
                )

                if main_content:
                    content = main_content.get_text(separator="\n", strip=True)
                    logger.info(f"✓ 使用 Web Scraping 成功获取 {len(content)} 字符")
                    return content
            except Exception as e:
                logger.warning(f"Web Scraping 失败: {e}")

        # 回退到 Jina Reader
        return self.fetch_with_jina(url)

    def fetch_github_repo(self, url: str) -> dict:
        """
        抓取 GitHub 仓库信息。

        Args:
            url: GitHub 仓库 URL

        Returns:
            包含仓库信息的字典
        """
        logger.info(f"Fetching GitHub repo: {url}")

        # 使用网页抓取
        content = self.fetch_webpage(url)

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
            result["content"] = self.fetch_webpage(url)

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
