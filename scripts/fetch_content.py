# Copyright (c) 2025
# 飞书链接发布器 - 内容抓取模块

"""抓取网页内容，支持微信公众号文章和普通网页。"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# 加载环境变量
try:
    from dotenv import load_dotenv
    skill_dir = Path(__file__).parent.parent
    env_path = skill_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# 尝试导入本地抓取器
try:
    from fetchers import JinaReaderFetcher, WeChatArticleFetcher, WebPageFetcher
    LOCAL_FETCHERS_AVAILABLE = True
except ImportError:
    LOCAL_FETCHERS_AVAILABLE = False
    logger.debug("Local fetchers not available")


class ContentFetcher:
    """网页内容抓取器。"""

    def __init__(self, jina_api_key: Optional[str] = None):
        """
        初始化抓取器。

        Args:
            jina_api_key: Jina API Key，可选
        """
        self.jina_api_key = jina_api_key
        if LOCAL_FETCHERS_AVAILABLE:
            self.jina_fetcher = JinaReaderFetcher(api_key=jina_api_key)
        else:
            self.jina_fetcher = None

    def fetch_with_jina(self, url: str) -> str:
        """
        使用 Jina Reader API 抓取网页内容。

        Args:
            url: 目标 URL

        Returns:
            网页内容
        """
        if self.jina_fetcher:
            result = self.jina_fetcher.fetch(url)
            if result["success"]:
                return result["content"]
            else:
                logger.error(f"Jina Reader 失败: {result.get('error')}")
                return ""
        return ""

    def fetch_wechat_article(self, url: str) -> dict:
        """抓取微信公众号文章"""
        logger.info(f"Fetching WeChat article: {url}")

        # 优先使用本地 WeChat 抓取器
        if LOCAL_FETCHERS_AVAILABLE:
            try:
                fetcher = WeChatArticleFetcher()
                result = fetcher.get_article(url)

                if result["success"]:
                    article_info = fetcher.format_content(result["content"])
                    logger.info(f"✓ 使用本地抓取器成功: {article_info['title']}")
                    return {
                        "url": url,
                        "title": article_info["title"],
                        "author": article_info["author"],
                        "content": "\n".join(article_info["texts"]),
                        "nickname": article_info["nickname"],
                        "createTime": article_info["createTime"],
                    }
                else:
                    logger.warning(f"本地抓取失败: {result.get('error')}")
            except Exception as e:
                logger.warning(f"本地抓取异常: {e}")

        # 如果有 Jina API Key，尝试使用
        if self.jina_api_key:
            logger.info("尝试使用 Jina Reader (with API key)")
            content = self.fetch_with_jina(url)
            if content:
                return {"url": url, "title": "微信文章", "content": content}

        # 兜底：使用 r.jina.ai
        logger.info("使用 r.jina.ai 作为兜底")
        content = self.fetch_with_jina(url)
        if content:
            return {"url": url, "title": "微信文章", "content": content}

        return {
            "url": url,
            "title": "微信文章（获取失败）",
            "content": f"⚠️ 无法获取微信文章\n\n{url}",
            "error": "fetch_failed",
        }

    def fetch_webpage(self, url: str) -> str:
        """抓取普通网页"""
        logger.info(f"Fetching webpage: {url}")

        # 优先使用 Jina Reader
        content = self.fetch_with_jina(url)
        if content:
            return content

        # 兜底：使用本地 Web 抓取器
        if LOCAL_FETCHERS_AVAILABLE:
            try:
                fetcher = WebPageFetcher()
                result = fetcher.fetch(url)

                if result["success"]:
                    logger.info(f"✓ 使用本地抓取器成功: {len(result['content'])} 字符")
                    return result["content"]
                else:
                    logger.warning(f"本地抓取失败: {result.get('error')}")
            except Exception as e:
                logger.warning(f"本地抓取异常: {e}")

        return ""

    def fetch_github_repo(self, url: str) -> dict:
        """抓取 GitHub 仓库"""
        logger.info(f"Fetching GitHub repo: {url}")

        content = self.fetch_webpage(url)

        pattern = r"github\.com/([^/]+)/([^/]+)"
        match = re.search(pattern, url)
        owner = repo = ""
        if match:
            owner = match.group(1)
            repo = match.group(2).replace(".git", "")

        return {"url": url, "owner": owner, "repo": repo, "content": content}

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


def main():
    parser = argparse.ArgumentParser(description="抓取网页内容")
    parser.add_argument("--url", required=True, help="目标 URL")
    parser.add_argument("--type", choices=["auto", "wechat", "github", "webpage"],
                       default="auto", help="链接类型，默认自动识别")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径")
    parser.add_argument("--jina-api-key", help="Jina API Key（可选）")

    args = parser.parse_args()

    fetcher = ContentFetcher(jina_api_key=args.jina_api_key)

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


if __name__ == "__main__":
    main()
