"""普通网页抓取器"""

import logging
import re

import requests
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 30


class WebPageFetcher:
    """普通网页抓取器"""

    def __init__(self):
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def fetch(self, url: str) -> dict:
        """抓取网页"""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=TIMEOUT,
                verify=False,
                allow_redirects=True
            )
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
                return {"success": True, "content": content}

            return {"success": False, "error": "无法提取内容"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "连接失败"}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP错误: {e.response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
