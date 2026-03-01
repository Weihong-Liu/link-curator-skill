---
name: link-curator
description: 智能链接策展工具 - 自动抓取、分析、整理和归档网页内容。支持微信公众号文章、GitHub 仓库、技术博客等各类链接的内容提取、摘要生成、封面制作和多维表格存储（飞书）。
---

# Link Curator - 智能链接策展工具

将任意链接的内容提取、分析、生成封面，并发布到飞书多维表格的完整流程。

## 适用场景

用户想要：
- 分析一个或多个链接并整理到飞书表格
- 从网页/公众号文章提取内容并生成摘要
- 自动生成封面图片并上传到飞书
- 批量处理链接并发布到飞书多维表格

## 处理流程

### 步骤 1：链接内容提取

**命令格式**：
```bash
cd /path/to/skills/link-curator
uv run python scripts/fetch_content.py --url "URL" --type auto
```

**支持的链接类型**：
- 微信公众号：自动使用本地 WeChat 抓取器
- GitHub 仓库：提取仓库信息和 README
- 普通网页：使用 Jina Reader API

**输出**：JSON 格式，包含 title、content、author 等字段

### 步骤 2：内容分析

由 LLM 直接分析提取的内容，生成：

1. **标题**：简洁明了，不超过 50 字
2. **摘要**：中文摘要，不超过 150 字
3. **类别**：选择 1-3 个类别
4. **评分**：0-100 分，根据内容价值
5. **封面风格**：选择最匹配的封面风格

**内容类别包括**：
- 技术文档: 编程、AI、开发工具等技术相关
- 文章博客: 个人博客、观点文章等
- 新闻资讯: 技术新闻、行业动态等
- 学习资源: 教程、课程、文档等
- 实用工具: 在线工具、软件服务等
- 产品介绍: 产品发布、更新说明等
- 微信文章: 微信公众号推送文章
- 代码仓库: GitHub/GitLab 等代码项目
- 其他: 不符合以上分类的内容

**封面风格可选值**：
- `swiss`: 瑞士国际 - 适合技术、工具、开发、AI、编程、代码、框架
- `acid`: 故障酸性 - 适合设计、创意、艺术、潮流、前卫
- `pop`: 波普撞色 - 适合新闻、热点、娱乐、有趣、趋势
- `shock`: 冲击波 - 适合警告、重要、必看、紧急、注意
- `diffuse`: 弥散光 - 适合生活、健康、情感、故事、清新
- `sticker`: 贴纸风 - 适合可爱、轻松、小技巧、日常、简单
- `journal`: 手账感 - 适合日记、记录、思考、感悟、文艺
- `cinema`: 电影感 - 适合深度、电影、故事、专题、叙事
- `tech`: 科技蓝 - 适合科技、数据、分析、报告、研究
- `minimal`: 极简白 - 适合极简、设计、美学、纯粹
- `memo`: 备忘录 - 适合笔记、清单、总结、备忘、实用
- `geek`: 极客黑 - 适合黑客、极客、编程、开发、系统

### 步骤 3：生成封面

**命令格式**：
```bash
cd /path/to/skills/link-curator
uv run python -m generate_cover_mcp.cli "标题文本" \
  --subtitle "精选内容·建议收藏" \
  --style swiss \
  --output cover.png \
  --output-dir covers
```

**参数说明**：
- 第一个参数：标题文本（位置参数，必需，不要用 `--title`）
- `--style`：封面风格（见上方列表）
- `--output`：输出文件名（不是 `--output-filename`）
- `--output-dir`：输出目录

### 步骤 4：发布到飞书

**命令格式**：
```bash
cd /path/to/skills/link-curator
uv run python scripts/publish_feishu.py \
  --title "标题" \
  --summary "摘要" \
  --url "原始链接" \
  --categories "类别1,类别2" \
  --cover "covers/cover.png"
```

**注意**：环境变量会自动从 `.env` 文件加载

## 飞书字段映射

发布到飞书时使用以下字段：

| 飞书字段 | 类型 | 说明 |
|---------|------|------|
| 标题 | 超链接 | 文本 + 原始链接 |
| 简介 | 文本 | 摘要内容 |
| 类型 | 多选 | 内容类别列表 |
| 分享者 | 文本 | 分享者名称（可选） |
| 创建日期 | 日期 | 毫秒时间戳（可选） |
| 封面 | 附件 | 封面图片文件（可选） |

## 环境配置

### 1. 配置环境变量

复制 `assets/.env.example` 到 `.env` 并填写配置：

```bash
cd /path/to/skills/link-curator
cp assets/.env.example .env
# 编辑 .env 文件，填写实际值
```

**必需配置**：
- `FEISHU_APP_ID`：飞书应用 ID
- `FEISHU_APP_SECRET`：飞书应用密钥
- `FEISHU_BASE_URL`：飞书多维表格 URL（必须设置为「互联网获得链接的人可编辑」权限）

**可选配置**：
- `JINA_API_KEY`：Jina API 密钥（不提供则使用免费的 r.jina.ai）

**Openclaw 用户**：如果使用 openclaw，`FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 会自动从 openclaw 配置读取，只需配置 `FEISHU_BASE_URL`。

### 2. 安装依赖

```bash
cd /path/to/skills/link-curator
uv venv
uv pip install -r assets/requirements.txt
```

### 3. 环境检查（可选）

```bash
cd /path/to/skills/link-curator
uv run python scripts/check_env.py
```

该脚本会检查 Python 版本、依赖包、环境变量、飞书连接等。

## 完整执行示例

**单个链接处理**：

```bash
cd /path/to/skills/link-curator

# 1. 提取内容
uv run python scripts/fetch_content.py \
  --url "https://mp.weixin.qq.com/s/xxx" \
  --type auto

# 2. 分析内容（由 LLM 完成）
# - 生成标题、摘要
# - 选择类别（1-3个）
# - 选择封面风格

# 3. 生成封面
uv run python -m generate_cover_mcp.cli \
  "文章标题" \
  --subtitle "精选内容·建议收藏" \
  --style swiss \
  --output article_cover.png \
  --output-dir covers

# 4. 发布到飞书
uv run python scripts/publish_feishu.py \
  --title "文章标题" \
  --url "https://mp.weixin.qq.com/s/xxx" \
  --summary "文章摘要内容..." \
  --categories "技术文档,学习资源" \
  --cover "covers/article_cover.png"
```

**批量处理**：对每个链接重复上述流程

## 常见问题

### 1. 环境变量未加载
**现象**：`飞书配置不完整，发布功能将被禁用`
**解决**：确保 `.env` 文件在 skill 目录下，脚本会自动加载

### 2. 封面生成 CLI 参数错误
**错误**：`unrecognized arguments: --title`
**原因**：title 是位置参数，不是选项参数
**正确**：`uv run python -m generate_cover_mcp.cli "标题" --output cover.png`

### 3. 依赖冲突
**现象**：`lark-oapi` 版本冲突
**解决**：在 skill 目录下创建独立虚拟环境：
```bash
cd /path/to/skills/link-curator
uv venv
uv pip install -r assets/requirements.txt
```

### 4. 飞书权限问题
**现象**：无法创建记录或上传封面
**解决**：确保 `FEISHU_BASE_URL` 对应的表格权限设置为「互联网获得链接的人可编辑」

## 最佳实践

1. **始终在 skill 目录下执行命令**：`cd /path/to/skills/link-curator`
2. **使用 `uv run python` 确保使用正确的虚拟环境**
3. **环境变量放在 skill 目录的 `.env` 文件中**
4. **封面生成使用 CLI 工具**：`python -m generate_cover_mcp.cli`
5. **检查 CLI 帮助确认参数格式**：`python -m xxx --help`

## MCP 依赖

此技能依赖以下 MCP 服务器：

1. **generate_cover_mcp**: 封面生成
   - 仓库：https://github.com/Weihong-Liu/generate_cover_mcp
   - 使用：见 `scripts/generate_cover.py`

2. **web_reader**: 网页内容读取
   - 内置 MCP，使用 `mcp__web_reader__webReader`
   - URL 前缀方式：`https://r.jina.ai/` + 原始 URL

3. **feishu_publisher**: 飞书发布
   - 使用 `scripts/publish_feishu.py` 中的封装函数
