"""内容抓取器模块"""

from .jina_fetcher import JinaReaderFetcher
from .wechat_fetcher import WeChatArticleFetcher
from .web_fetcher import WebPageFetcher

__all__ = ["WeChatArticleFetcher", "WebPageFetcher", "JinaReaderFetcher"]
