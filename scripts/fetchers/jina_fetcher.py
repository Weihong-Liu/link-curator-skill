"""Jina Reader API 抓取器"""

import logging
import re

import requests
from markdown_it import MarkdownIt

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

JINA_BASE_URL = "https://r.jina.ai"
TIMEOUT = 60

md = MarkdownIt("commonmark")


def strip_markdown_links(markdown: str) -> str:
    """移除 markdown 中的链接，保留文本内容"""
    tokens = md.parse(markdown)

    def render(ts):
        out = []
        for tok in ts:
            t = tok.type

            if t == "link_open" or t == "link_close":
                continue

            if t == "image":
                continue

            if t == "softbreak":
                out.append("\n")
                continue
            if t == "hardbreak":
                out.append("\n")
                continue
            if t in ("paragraph_close", "heading_close", "blockquote_close"):
                out.append("\n\n")
                continue
            if t in ("list_item_close", "bullet_list_close", "ordered_list_close"):
                out.append("\n")
                continue
            if t == "hr":
                out.append("\n\n")
                continue

            if tok.children:
                out.append(render(tok.children))
                continue

            if t == "code_inline":
                out.append(f"`{tok.content}`")
            else:
                out.append(tok.content or "")

        return "".join(out)

    text = render(tokens)
    text = re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"
    return text.strip()


class JinaReaderFetcher:
    """Jina Reader API 抓取器"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = JINA_BASE_URL
        self.timeout = TIMEOUT

    def fetch(self, url: str) -> dict:
        """使用 Jina Reader API 抓取网页"""
        if not url or not url.startswith(("http://", "https://")):
            return {"success": False, "error": f"Invalid URL: {url}"}

        # 避免重复的 Jina URL 前缀
        if url.startswith("https://r.jina.ai/") and url.count("http") >= 2:
            url = url[len("https://r.jina.ai/"):]

        try:
            jina_url = f"{self.base_url}/{url}"
            headers = {}

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                logger.info(f"使用 Jina Reader API (with key): {jina_url}")
            else:
                logger.info(f"使用 Jina Reader API (without key): {jina_url}")

            response = requests.get(jina_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            content = response.text.strip()
            content = strip_markdown_links(content)

            if not content:
                return {"success": False, "error": "No content retrieved"}

            return {"success": True, "content": content}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "连接失败"}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP错误: {e.response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
