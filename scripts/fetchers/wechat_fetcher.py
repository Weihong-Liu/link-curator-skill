"""微信公众号文章抓取器"""

import logging
import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

try:
    USER_AGENT = UserAgent().chrome
except Exception:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class WeChatArticleFetcher:
    """微信公众号文章抓取器"""

    def __init__(self):
        self.session = requests.Session()
        self.timeout = 10
        self.headers = {"User-Agent": USER_AGENT}

    def get_article(self, url: str) -> dict:
        """抓取微信文章"""
        try:
            url = url.replace('amp;', '')
            res = self.session.get(
                url=url,
                headers=self.headers,
                verify=False,
                timeout=self.timeout
            )

            if "var createTime = " in res.text:
                return {"success": True, "content": res.text}
            elif ">当前环境异常" in res.text:
                return {"success": False, "error": "需要验证"}
            elif "操作频繁" in res.text:
                return {"success": False, "error": "操作频繁"}
            else:
                return {"success": False, "error": "未知错误"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def format_content(self, html: str) -> dict:
        """格式化文章内容"""
        soup = BeautifulSoup(html, "lxml")

        nickname = soup.find("a", id="js_name").get_text().strip()
        author = soup.find("meta", {"name": "author"}).get("content").strip()
        article_link = soup.find("meta", property="og:url").get("content")
        title = soup.find("h1", id="activity-name").get_text().strip()

        texts = soup.getText().split("\n")
        texts = list(filter(lambda x: bool(x.strip()), texts))

        createTime = re.search(r"var createTime = '(.*?)'.*", html).group(1)

        return {
            "nickname": nickname,
            "author": author,
            "article_link": article_link,
            "title": title,
            "createTime": createTime,
            "content": html,
            "texts": texts,
        }
