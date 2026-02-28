# 快速开始示例

## 1. 配置环境

### 方式 A: 自动环境设置（推荐）

```bash
# 运行环境检查和自动安装
python -m scripts.setup --install
```

这会自动：
- 检查 Python 版本
- 安装 uv（包管理工具）
- 创建虚拟环境
- 安装所需依赖
- 创建 .env 配置文件模板

### 方式 B: 手动安装

```bash
# 安装 uv
pip install uv

# 创建虚拟环境
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
uv pip install -r assets/requirements.txt

# 配置环境变量
cp assets/.env.example .env
# 编辑 .env 填入飞书配置
```

## 2. 使用方式

### 方式 1: 直接调用脚本

```bash
# 抓取内容
python -m scripts.fetch_content --url "https://github.com/anthropics/claude-code-skills"

# 生成封面
python -m scripts.generate_cover --title "标题" --style swiss

# 发布到飞书
python -m scripts.publish_feishu \
  --title "标题" \
  --url "https://example.com" \
  --summary "摘要" \
  --categories "技术,工具"
```

### 方式 2: 使用完整流程

```bash
# 单个链接
python -m scripts.pipeline --url "https://example.com"

# 批量处理
python -m scripts.pipeline --urls "https://a.com,https://b.com"

# 从文件读取链接
python -m scripts.pipeline --url-file urls.txt

# 测试模式（不发布）
python -m scripts.pipeline --url "https://example.com" --dry-run
```

### 方式 3: 通过 Claude Code 使用

在 Claude Code 中：

```
帮我分析这个链接并发布到飞书：https://github.com/anthropics/claude-code-skills
```

```
批量处理这些链接：
- https://mp.weixin.qq.com/s/xxx
- https://github.com/xxx/yyy
```

## 3. 链接格式示例

| 类型 | 示例 |
|-----|------|
| 微信文章 | `https://mp.weixin.qq.com/s/xxxxx` |
| GitHub 仓库 | `https://github.com/user/repo` |
| 技术文章 | `https://juejin.cn/post/12345` |
| 普通网页 | `https://example.com/article` |

## 4. 飞书表格字段

确保飞书多维表格包含以下字段：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| 标题 | 超链接 | 链接文本 + URL |
| 简介 | 文本 | 内容摘要 |
| 类型 | 多选 | 分类标签 |
| 分享者 | 文本 | 可选 |
| 创建日期 | 日期 | 可选 |
| 封面 | 附件 | 可选 |
