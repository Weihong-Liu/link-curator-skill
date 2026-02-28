# Copyright (c) 2025
# 飞书链接发布器 - 飞书发布模块

"""发布到飞书多维表格。"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    import lark_oapi as lark
    from lark_oapi.api.bitable.v1 import *
    from lark_oapi.api.drive.v1 import *
except ImportError:
    print("Error: lark-oapi package not installed. Please install: pip install lark-oapi")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_bitable_app_token(url: str) -> str:
    """
    从飞书多维表格（Base）URL 中解析 app_token

    示例：
    https://xxx.feishu.cn/base/IYyBxxxxxx?from=xxx
    -> IYyBxxxxxx
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    if "base" not in path_parts:
        raise ValueError("该 URL 不是飞书多维表格（Base）链接")

    base_index = path_parts.index("base")

    try:
        app_token = path_parts[base_index + 1]
    except IndexError:
        raise ValueError("未能从 URL 中解析出 app_token")

    return app_token


def datetime_to_unix_ms(dt: datetime) -> int:
    """datetime -> Unix 时间戳（毫秒）"""
    return int(dt.timestamp() * 1000)


class FeishuClient:
    """飞书客户端封装。"""

    def __init__(self, app_id: str, app_secret: str):
        self.client = (
            lark.Client.builder()
            .app_id(app_id)
            .app_secret(app_secret)
            .log_level(lark.LogLevel.INFO)
            .build()
        )


class FeishuFileUploader:
    """飞书文件上传服务。"""

    def __init__(self, feishu_client: FeishuClient):
        self.client = feishu_client.client

    def upload_image_to_bitable(self, file_path: str, app_token: str) -> str:
        """
        上传图片到多维表格，返回 file_token
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        file = open(file_path, "rb")

        request: UploadAllMediaRequest = (
            UploadAllMediaRequest.builder()
            .request_body(
                UploadAllMediaRequestBody.builder()
                .file_name(os.path.basename(file_path))
                .parent_type("bitable_image")
                .parent_node(app_token)
                .size(os.path.getsize(file_path))
                .file(file)
                .build()
            )
            .build()
        )

        response: UploadAllMediaResponse = self.client.drive.v1.media.upload_all(request)

        if not response.success():
            raise RuntimeError(
                f"upload_all failed, code={response.code}, msg={response.msg}, "
                f"log_id={response.get_log_id()}"
            )

        return response.data.file_token


class FeishuBaseService:
    """飞书多维表格 Base 服务。"""

    def __init__(
        self,
        feishu_client: FeishuClient,
        app_token: str,
        table_id: Optional[str] = None,
        table_name: Optional[str] = None,
        auto_pick_first: bool = True
    ):
        self.client = feishu_client.client
        self.app_token = app_token

        if table_id:
            self.table_id = table_id
        elif table_name:
            self.table_id = self.get_table_id_by_name(table_name)
        else:
            tables = self.list_tables()
            if not tables:
                raise RuntimeError("该多维表格下没有任何数据表")

            if not auto_pick_first:
                raise RuntimeError("未指定 table_id / table_name")

            self.table_id = tables[0].table_id

    def list_tables(self) -> list:
        """列出所有数据表。"""
        tables = []
        page_token = None

        while True:
            request = (
                ListAppTableRequest.builder()
                .app_token(self.app_token)
                .page_size(100)
                .build()
            )

            response = self.client.bitable.v1.app_table.list(request)

            if not response.success():
                raise RuntimeError(
                    f"list_tables failed, code={response.code}, msg={response.msg}"
                )

            data = response.data
            tables.extend(data.items)

            if not data.has_more:
                break

            page_token = data.page_token

        return tables

    def get_table_id_by_name(self, table_name: str) -> str:
        """按表名查 table_id。"""
        for table in self.list_tables():
            if table.name == table_name:
                return table.table_id
        raise ValueError(f"未找到数据表: {table_name}")

    def create_record(self, fields: dict):
        """新增一条记录。"""
        request: CreateAppTableRecordRequest = (
            CreateAppTableRecordRequest.builder()
            .app_token(self.app_token)
            .table_id(self.table_id)
            .ignore_consistency_check(True)
            .request_body(
                AppTableRecord.builder()
                .fields(fields)
                .build()
            )
            .build()
        )

        response: CreateAppTableRecordResponse = (
            self.client.bitable.v1.app_table_record.create(request)
        )

        if not response.success():
            raise RuntimeError(
                f"create_record failed, code={response.code}, msg={response.msg}"
            )

        return response.data


class FeishuPublisher:
    """飞书链接发布器。"""

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化飞书发布器。

        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            base_url: 飞书多维表格 URL
        """
        # 从环境变量读取配置
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self.base_url = base_url or os.getenv("FEISHU_BASE_URL")

        if not all([self.app_id, self.app_secret, self.base_url]):
            logger.warning("飞书配置不完整，发布功能将被禁用")
            self.enabled = False
            return

        self.enabled = True
        self._init_client()

    def _init_client(self):
        """初始化飞书客户端。"""
        try:
            self.app_token = parse_bitable_app_token(self.base_url)
            self.feishu_client = FeishuClient(self.app_id, self.app_secret)
            self.base_service = FeishuBaseService(self.feishu_client, self.app_token)
            self.file_uploader = FeishuFileUploader(self.feishu_client)
            logger.info(f"已连接到飞书 Base: {self.base_url}")
        except Exception as e:
            logger.error(f"飞书客户端初始化失败: {e}")
            self.enabled = False

    def publish(
        self,
        title: str,
        url: str,
        summary: str,
        categories: List[str],
        cover_path: Optional[str] = None,
        sender: Optional[str] = None,
        created_at: Optional[int] = None,
    ) -> bool:
        """
        发布单条记录到飞书。

        Args:
            title: 标题
            url: 原始链接
            summary: 摘要
            categories: 类别列表
            cover_path: 封面图片路径
            sender: 分享者
            created_at: 创建时间（毫秒时间戳）

        Returns:
            是否成功
        """
        if not self.enabled:
            logger.warning("飞书发布未启用")
            return False

        try:
            # 构建字段
            fields = {
                "标题": {
                    "text": title or url[:50],
                    "link": url
                },
                "简介": summary,
                "类型": categories or ["其他"],
            }

            if sender:
                fields["分享者"] = sender

            if created_at:
                fields["创建日期"] = created_at
            else:
                fields["创建日期"] = datetime_to_unix_ms(datetime.now())

            # 上传封面
            if cover_path and os.path.exists(cover_path):
                try:
                    file_token = self.file_uploader.upload_image_to_bitable(
                        cover_path, self.app_token
                    )
                    fields["封面"] = [{"file_token": file_token}]
                    logger.info(f"封面已上传: {cover_path}")
                except Exception as e:
                    logger.warning(f"封面上传失败: {e}")

            # 创建记录
            self.base_service.create_record(fields)
            logger.info(f"✓ 已发布到飞书: {title[:30]}")
            return True

        except Exception as e:
            logger.error(f"发布失败: {e}")
            return False

    def publish_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        批量发布记录。

        Args:
            records: 记录列表，每个记录包含 title, url, summary, categories,
                     cover_path, sender, created_at 等字段

        Returns:
            成功发布的记录数
        """
        if not self.enabled:
            logger.warning("飞书发布未启用")
            return 0

        success_count = 0
        for idx, record in enumerate(records, 1):
            logger.info(f"[{idx}/{len(records)}] 处理中: {record.get('title', record.get('url', ''))[:30]}")

            if self.publish(
                title=record.get("title", ""),
                url=record.get("url", ""),
                summary=record.get("summary", ""),
                categories=record.get("categories", []),
                cover_path=record.get("cover_path"),
                sender=record.get("sender"),
                created_at=record.get("created_at"),
            ):
                success_count += 1

        logger.info(f"发布完成: {success_count}/{len(records)}")
        return success_count


def main():
    parser = argparse.ArgumentParser(description="发布到飞书多维表格")
    parser.add_argument("--title", help="标题")
    parser.add_argument("--url", help="原始链接")
    parser.add_argument("--summary", help="摘要")
    parser.add_argument("--categories", help="类别，逗号分隔")
    parser.add_argument("--cover", help="封面图片路径")
    parser.add_argument("--sender", help="分享者")
    parser.add_argument("--json", help="从 JSON 文件读取记录")
    parser.add_argument("--dry-run", action="store_true", help="只验证不发布")

    args = parser.parse_args()

    publisher = FeishuPublisher()

    if not publisher.enabled:
        logger.error("飞书发布未启用，请检查环境变量配置")
        sys.exit(1)

    if args.json:
        # 从 JSON 文件批量发布
        json_path = Path(args.json)
        records = json.loads(json_path.read_text(encoding="utf-8"))

        if args.dry_run:
            logger.info(f"Dry run 模式，将发布 {len(records)} 条记录")
            for r in records[:3]:
                logger.info(f"  - {r.get('title', r.get('url', ''))[:50]}")
            return

        publisher.publish_batch(records)

    else:
        # 单条发布
        if not all([args.title, args.url, args.summary]):
            logger.error("缺少必要参数: title, url, summary")
            sys.exit(1)

        categories = args.categories.split(",") if args.categories else ["其他"]

        if args.dry_run:
            logger.info("Dry run 模式:")
            logger.info(f"  标题: {args.title}")
            logger.info(f"  链接: {args.url}")
            logger.info(f"  摘要: {args.summary[:50]}...")
            logger.info(f"  类别: {categories}")
            logger.info(f"  封面: {args.cover or '无'}")
            return

        publisher.publish(
            title=args.title,
            url=args.url,
            summary=args.summary,
            categories=categories,
            cover_path=args.cover,
            sender=args.sender,
        )


if __name__ == "__main__":
    main()
