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

根据链接类型使用对应方法提取内容：

**普通网页/技术文章**
```python
python -m scripts.fetch_content --url "https://example.com"
```
使用方法：
- 优先使用 `scripts/fetch_content.py` 中的 `fetch_with_jina()` 函数
- 在 URL 前加 `https://r.jina.ai/` 前缀即可获取 markdown 格式内容
- 示例：`https://r.jina.ai/https://github.com/xxx/yyy`

**微信公众号文章**
```python
python -m scripts.fetch_content --url "https://mp.weixin.qq.com/s/xxx" --type wechat
```
使用方法：
- 调用 `scripts/fetch_content.py` 中的 `fetch_wechat_article()` 函数
- 需要使用微信文章专用 MCP 处理

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

使用封面生成 MCP：
```python
python -m scripts.generate_cover --title "标题" --style swiss --output covers/cover.png
```

调用 `scripts/generate_cover.py` 中的 `generate_cover()` 函数，参数：
- `title`: 标题文本
- `subtitle`: 副标题（默认 "精选内容·建议收藏"）
- `style`: 封面风格（见上方列表）
- `output`: 输出路径

### 步骤 4：发布到飞书

使用飞书发布脚本：
```python
python -m scripts.publish_feishu \
  --title "标题" \
  --summary "摘要" \
  --url "原始链接" \
  --categories "类别1,类别2" \
  --cover "covers/cover.png"
```

调用 `scripts/publish_feishu.py` 中的 `publish_to_feishu()` 函数。

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

## 环境配置与检查

### 自动环境检查（推荐）

**首次使用前必须运行环境检查**：

```bash
uv run python -m scripts.check_env
```

该脚本会检查：
1. ✓ Python 版本（需要 3.10+）
2. ✓ 依赖包（httpx, lark_oapi, playwright, mcp）
3. ✓ 环境变量（脱敏显示，不泄露具体值）
4. ✓ Playwright 浏览器（封面生成需要）
5. ✓ 飞书 API 连接测试
6. ✓ 飞书多维表格字段验证
7. ✓ 飞书应用权限提示

**如果检查失败**，脚本会给出详细的修复建议。

### 依赖安装

如果缺少依赖包，运行：
```bash
python -m scripts.setup --install
```

### 手动配置

需要配置以下环境变量（在项目根目录的 `.env` 文件中）：

```bash
# 飞书配置
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_BASE_URL=https://xxx.feishu.cn/base/app_token

# Jina API（可选，不提供则使用 r.jina.ai 前缀方式）
JINA_API_KEY=your_jina_api_key
```

### 安装依赖

使用 uv（推荐）：
```bash
pip install uv
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r assets/requirements.txt
```

或使用 pip：
```bash
pip install -r assets/requirements.txt
```

## 使用示例

**单个链接处理**：
```
用户：帮我分析这个链接并发布到飞书 https://github.com/anthropics/claude-code-skills

处理流程：
0. 自动检查环境（首次使用或环境变量缺失时）
1. 使用 fetch_with_jina() 提取内容
2. LLM 分析生成标题、摘要、类别、封面风格
3. 生成封面图片
4. 发布到飞书
```

**环境检查失败时**：
- 如果缺少环境变量，会自动询问用户提供
- 如果缺少依赖，会提示安装命令
- 如果飞书字段不匹配，会列出缺失字段
- 如果权限未开启，会提示开启权限

**批量处理**：
```
用户：批量处理这些链接并发布到飞书：
- https://mp.weixin.qq.com/s/xxx
- https://github.com/xxx/yyy
- https://juejin.cn/post/zzz

处理流程：
对每个链接执行上述完整流程
```

## 注意事项

1. **内容提取优先级**：
   - 微信文章：使用专用 MCP
   - 其他链接：使用 `https://r.jina.ai/` 前缀

2. **分类选择**：
   - 根据链接域名和内容关键词智能分类
   - 支持多选，但建议 1-3 个

3. **封面风格选择**：
   - 根据类别和标题关键词自动选择
   - 技术/代码类默认 `swiss`
   - 设计/艺术类默认 `acid`

4. **错误处理**：
   - 如果内容提取失败，使用 URL 的域名作为标题
   - 如果封面生成失败，跳过封面继续发布
   - 如果飞书发布失败，记录错误并处理下一个

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
