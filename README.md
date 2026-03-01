# Link Curator

> 智能链接策展工具 - 自动抓取、分析、整理和归档网页内容

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Link Curator 是一个智能链接收藏和整理工具，可以自动从任意 URL 提取内容、生成摘要、创建精美封面，并将其归档到你选择的存储后端（目前支持飞书多维表格）。

## ✨ 特性

- 🌐 **智能内容提取** - 支持普通网页、GitHub 仓库、微信公众号文章等
- 🤖 **AI 驱动分析** - 自动生成标题、摘要、分类和标签
- 🎨 **自动封面生成** - 12 种风格，根据内容自动选择最佳风格
- 📊 **多维表格存储** - 支持飞书多维表格，易于管理和检索
- ✅ **完整环境检查** - 自动检查依赖、配置和权限
- 🔄 **批量处理** - 支持一次处理多个链接

## 🚀 快速开始

### 安装

```bash
# 进入 skill 目录
cd /path/to/skills/link-curator

# 创建虚拟环境并安装依赖
uv venv
uv pip install -r assets/requirements.txt
```

### 配置

1. 复制环境变量模板：
```bash
cp assets/.env.example .env
```

2. 编辑 `.env` 文件，填写飞书配置：
```bash
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_BASE_URL=https://xxx.feishu.cn/base/app_token
```

**重要**：
- `.env` 文件必须放在 skill 目录下
- 脚本会自动加载此文件，无需手动设置环境变量
- `FEISHU_BASE_URL` 对应的表格必须设置为「互联网获得链接的人可编辑」权限

3. 运行环境检查（可选）：
```bash
uv run python scripts/check_env.py
```

### 使用

#### 作为 Claude Code Skill 使用

在 Claude Code 中直接使用：

```
帮我整理这个链接并保存到飞书：https://mp.weixin.qq.com/s/xxx
```

#### 命令行使用

**重要**：所有命令都必须在 skill 目录下执行

```bash
cd /path/to/skills/link-curator

# 1. 提取内容
uv run python scripts/fetch_content.py --url "URL" --type auto

# 2. 生成封面（注意：title 是位置参数）
uv run python -m generate_cover_mcp.cli "标题" --style swiss --output cover.png

# 3. 发布到飞书
uv run python scripts/publish_feishu.py \
  --title "标题" \
  --url "URL" \
  --summary "摘要" \
  --categories "类别1,类别2" \
  --cover "covers/cover.png"
```

## 📖 详细文档

### 常见问题

#### 1. 环境变量未加载？
**现象**：`飞书配置不完整，发布功能将被禁用`

**解决**：
- 确保 `.env` 文件在 skill 目录下
- 脚本会自动使用 `python-dotenv` 加载环境变量
- 不需要手动 `export` 或使用 `source`

#### 2. 封面生成 CLI 参数错误？
**现象**：`unrecognized arguments: --title`

**原因**：title 是位置参数，不是选项参数

**正确用法**：
```bash
# ✓ 正确
uv run python -m generate_cover_mcp.cli "标题" --output cover.png

# ✗ 错误
uv run python -m generate_cover_mcp.cli --title "标题" --output-filename cover.png
```

#### 3. 依赖冲突？
**现象**：`lark-oapi` 版本冲突

**解决**：在 skill 目录下创建独立虚拟环境
```bash
cd /path/to/skills/link-curator
uv venv
uv pip install -r assets/requirements.txt
```

#### 4. 飞书权限问题？
**现象**：无法创建记录或上传封面

**解决**：
1. 打开飞书多维表格
2. 点击右上角「分享」
3. 设置为「互联网获得链接的人可编辑」
4. 复制链接作为 `FEISHU_BASE_URL`

#### 5. 工作目录错误？
**现象**：`No module named scripts.xxx`

**解决**：始终在 skill 目录下执行命令
```bash
cd /path/to/skills/link-curator
uv run python scripts/xxx.py
```

### 环境检查

运行完整的环境检查：

```bash
cd /path/to/skills/link-curator
uv run python scripts/check_env.py
```

检查内容包括：
- ✓ Python 版本（需要 3.10+）
- ✓ 依赖包（httpx, lark_oapi, playwright, mcp）
- ✓ 环境变量（脱敏显示）
- ✓ Playwright 浏览器
- ✓ 飞书 API 连接
- ✓ 飞书多维表格字段验证
- ✓ 飞书应用权限提示

### 封面风格

支持 12 种封面风格，自动根据内容选择：

| 风格 | 适用场景 |
|------|---------|
| `swiss` | 技术、工具、开发、AI、编程 |
| `acid` | 设计、创意、艺术、潮流 |
| `pop` | 新闻、热点、娱乐、趋势 |
| `shock` | 警告、重要、必看、紧急 |
| `diffuse` | 生活、健康、情感、故事 |
| `sticker` | 可爱、轻松、小技巧、日常 |
| `journal` | 日记、记录、思考、感悟 |
| `cinema` | 深度、电影、故事、专题 |
| `tech` | 科技、数据、分析、报告 |
| `minimal` | 极简、设计、美学、纯粹 |
| `memo` | 笔记、清单、总结、备忘 |
| `geek` | 黑客、极客、编程、系统 |

### 飞书表格字段

需要在飞书多维表格中创建以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 标题 | 超链接 | 文章标题 + 原始链接 |
| 简介 | 文本 | 内容摘要 |
| 类型 | 多选 | 内容分类 |
| 分享者 | 文本 | 分享者名称（可选） |
| 创建日期 | 日期 | 创建时间戳 |
| 封面 | 附件 | 封面图片 |

### 飞书应用权限

需要在飞书开放平台开启以下权限：

- `bitable:app` - 多维表格读写
- `drive:drive` - 云文档读写（上传封面）

## 🛠️ 开发

### 项目结构

```
link-curator/
├── scripts/              # Python 脚本
│   ├── check_env.py     # 环境检查
│   ├── env_helper.py    # 环境辅助函数
│   ├── fetch_content.py # 内容抓取
│   ├── generate_cover.py # 封面生成
│   ├── publish_feishu.py # 飞书发布
│   └── pipeline.py      # 完整流程
├── assets/              # 资源文件
│   ├── requirements.txt # Python 依赖
│   └── .env.example     # 环境变量模板
├── SKILL.md            # Claude Code Skill 定义
└── README.md           # 本文件
```

### 运行测试

```bash
cd /path/to/skills/link-curator

# 测试内容抓取
uv run python scripts/fetch_content.py --url "https://example.com" --type auto

# 测试封面生成
uv run python -m generate_cover_mcp.cli "测试标题" --style swiss --output test.png

# 测试飞书发布
uv run python scripts/publish_feishu.py \
  --title "测试" \
  --url "https://example.com" \
  --summary "测试摘要" \
  --categories "测试"
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [generate_cover_mcp](https://github.com/Weihong-Liu/generate_cover_mcp) - 封面生成
- [Jina AI](https://jina.ai/) - 网页内容提取
- [飞书开放平台](https://open.feishu.cn/) - 数据存储

## 📮 联系

如有问题或建议，请提交 [Issue](https://github.com/Weihong-Liu/link-curator-skill/issues)

