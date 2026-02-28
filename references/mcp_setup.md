# MCP 依赖配置

此技能依赖以下 MCP 服务器：

## 1. generate_cover_mcp

封面生成 MCP 服务器。

**仓库**: https://github.com/Weihong-Liu/generate_cover_mcp

**安装**:
```bash
pip install generate-cover-mcp
```

**使用方法**:
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "generate_cover_mcp"],
)

async with stdio_client(server_params) as session:
    result = await session.call_tool(
        "generate_cover",
        arguments={
            "title": "标题",
            "subtitle": "副标题",
            "style": "swiss",
            "output": "cover.png",
        }
    )
```

**可用风格**:
- `swiss`: 瑞士国际
- `acid`: 故障酸性
- `pop`: 波普撞色
- `shock`: 冲击波
- `diffuse`: 弥散光
- `sticker`: 贴纸风
- `journal`: 手账感
- `cinema`: 电影感
- `tech`: 科技蓝
- `minimal`: 极简白
- `memo`: 备忘录
- `geek`: 极客黑

## 2. web_reader (内置)

网页内容读取 MCP。

**使用方法**:
- 直接使用 `https://r.jina.ai/` 前缀
- 示例: `https://r.jina.ai/https://github.com/xxx/yyy`

**说明**:
不需要 API Key，直接在 URL 前加前缀即可获取 markdown 格式内容。

## 3. 飞书 API

使用 `lark-oapi` SDK 直接调用飞书 API。

**安装**:
```bash
pip install lark-oapi
```

**配置**:
```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_BASE_URL="https://xxx.feishu.cn/base/app_token"
```
