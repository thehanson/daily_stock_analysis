# IBKR 新闻功能集成指南

本文档说明如何使用 Interactive Brokers (IBKR) 的新闻功能获取股票相关新闻。

## 目录

- [功能概述](#功能概述)
- [前置条件](#前置条件)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [API 参考](#api-参考)
- [集成到分析流程](#集成到分析流程)
- [故障排查](#故障排查)

---

## 功能概述

IBKR 新闻功能提供：

- **券商级别新闻源**：来自 Briefing.com、Dow Jones、The Fly 等专业新闻提供商
- **实时更新**：新闻数据实时同步
- **全球市场覆盖**：支持美股、港股、A股（通过港股通）
- **结构化数据**：标题、时间、来源、情绪分析等
- **完整文章内容**：可获取新闻的完整正文

### 可用新闻提供商

| 代码 | 名称 | 说明 |
|------|------|------|
| `BRFUPDN` | Briefing.com | 专业财经新闻 |
| `BRFG` | Briefing General | 综合财经资讯 |
| `DJ-N` | Dow Jones | 道琼斯新闻 |
| `DJ-RT` | Dow Jones Real-Time | 道琼斯实时新闻 |
| `FLY` | The Fly | 市场快讯 |
| `MT_NEWSWIRES` | MT Newswires | MT 新闻专线 |
| `BENZINGA` | Benzinga | Benzinga 财经新闻 |

**注意**：可用的新闻提供商取决于你的 IBKR 账户订阅。

---

## 前置条件

### 1. IBKR 账户

- 拥有 Interactive Brokers 账户
- 账户已激活并可以登录 TWS 或 IB Gateway
- 订阅了新闻数据服务（部分新闻源可能需要额外订阅）

### 2. 本地环境

- **TWS (Trader Workstation)** 或 **IB Gateway** 正在运行
- 已启用 API 连接（在 TWS/Gateway 设置中）
- Python 环境已安装 `ib_insync`：

```bash
pip install ib_insync
```

### 3. 网络要求

- 本地运行（不支持 GitHub Actions 等云环境）
- TWS/Gateway 需要能够连接到 IBKR 服务器

---

## 配置说明

### 环境变量

在 `.env` 文件中添加以下配置：

```bash
# IBKR 连接配置
IBKR_HOST=127.0.0.1          # TWS/Gateway 地址
IBKR_PORT=7497               # TWS=7497, Gateway=4001/4002
IBKR_CLIENT_ID=1             # 客户端ID（1-32之间）
IBKR_TIMEOUT=10              # 连接超时（秒）

# IBKR 新闻功能开关
IBKR_NEWS_ENABLED=true       # 启用 IBKR 新闻功能
```

### 端口说明

| 应用 | 实盘端口 | 模拟盘端口 |
|------|----------|------------|
| TWS | 7497 | 7497 |
| IB Gateway | 4001 | 4002 |

### TWS/Gateway 设置

1. 打开 TWS 或 IB Gateway
2. 进入 **File → Global Configuration → API → Settings**
3. 勾选 **Enable ActiveX and Socket Clients**
4. 设置 **Socket port**（如 7497）
5. 勾选 **Allow connections from localhost only**（推荐）
6. 点击 **OK** 保存

---

## 使用方法

### 1. 基础用法

```python
from src.news_providers.ibkr_news_provider import IBKRNewsProvider

# 创建提供商实例
provider = IBKRNewsProvider()

# 检查是否可用
if not provider.is_available():
    print("IBKR 新闻功能不可用")
    exit(1)

# 获取股票新闻
news_list = provider.get_stock_news(
    stock_code="AAPL",
    max_results=10,
    days=7
)

# 打印新闻
for news in news_list:
    print(f"{news['time']}: {news['headline']}")
    print(f"来源: {news['provider_name']}")
    print()
```

### 2. 获取完整文章内容

```python
# 获取新闻列表
news_list = provider.get_stock_news("AAPL", max_results=5, days=7)

# 获取第一条新闻的完整内容
if news_list:
    first_news = news_list[0]
    content = provider.get_news_article(
        article_id=first_news['article_id'],
        provider_code=first_news['provider_code']
    )
    
    if content:
        print(f"标题: {first_news['headline']}")
        print(f"内容:\n{content}")
```

### 3. 指定新闻提供商

```python
# 只使用 Dow Jones 和 Briefing.com
news_list = provider.get_stock_news(
    stock_code="AAPL",
    max_results=10,
    days=7,
    providers=['DJ-N', 'BRFUPDN']
)
```

### 4. 便捷函数

```python
from src.news_providers import get_ibkr_news, get_ibkr_article

# 快速获取新闻
news = get_ibkr_news("AAPL", max_results=10, days=7)

# 快速获取文章
content = get_ibkr_article(article_id="...", provider_code="DJ-N")
```

---

## API 参考

### IBKRNewsProvider

#### `__init__()`

创建 IBKR 新闻提供商实例。

#### `is_available() -> bool`

检查 IBKR 新闻功能是否可用。

**返回**：
- `True`：功能可用
- `False`：功能不可用（未安装 ib_insync、未启用、或未连接）

#### `get_news_providers() -> List[str]`

获取可用的新闻提供商列表。

**返回**：
- 新闻提供商代码列表，如 `['BRFUPDN', 'DJ-N', 'FLY']`

#### `get_stock_news(stock_code, max_results=10, days=7, providers=None) -> List[Dict]`

获取股票相关新闻。

**参数**：
- `stock_code` (str)：股票代码（如 `AAPL`, `600519`, `0700.HK`）
- `max_results` (int)：最大返回数量（默认 10）
- `days` (int)：查询天数（默认 7）
- `providers` (List[str], optional)：新闻提供商列表（默认使用所有可用提供商）

**返回**：
新闻列表，每条新闻包含：
```python
{
    'article_id': str,        # 文章ID
    'headline': str,          # 标题
    'time': str,              # 发布时间（ISO 8601 格式）
    'provider_code': str,     # 新闻提供商代码
    'provider_name': str,     # 新闻提供商名称
    'sentiment': str | None,  # 情绪（如果可用）
}
```

#### `get_news_article(article_id, provider_code) -> Optional[str]`

获取新闻文章完整内容。

**参数**：
- `article_id` (str)：文章ID（从 `get_stock_news` 返回）
- `provider_code` (str)：新闻提供商代码

**返回**：
- 文章内容（纯文本或 HTML）
- 失败返回 `None`

---

## 集成到分析流程

### 方案 1：作为独立新闻源

在 `src/search_service.py` 中添加 IBKR 新闻作为一个独立的新闻维度：

```python
def search_comprehensive_intel(self, stock_code: str, stock_name: str, max_searches: int = 3):
    """综合情报搜索"""
    intel_results = {}
    
    # 现有维度：latest_news, market_analysis, risk_check
    # ...
    
    # 新增：IBKR 新闻维度
    if self._is_ibkr_news_available():
        ibkr_news = self._search_ibkr_news(stock_code, stock_name)
        if ibkr_news.success:
            intel_results['ibkr_news'] = ibkr_news
    
    return intel_results
```

### 方案 2：作为新闻源的补充

在现有的 `search_stock_news` 方法中，将 IBKR 新闻作为补充数据源：

```python
def search_stock_news(self, stock_code: str, stock_name: str, max_results: int = 5):
    """搜索股票新闻"""
    # 现有搜索逻辑
    response = self._run_provider_search(...)
    
    # 补充 IBKR 新闻
    if self._is_ibkr_news_available():
        ibkr_news = self._get_ibkr_news(stock_code, max_results=5)
        response.results.extend(ibkr_news)
    
    return response
```

### 方案 3：优先使用 IBKR 新闻

对于美股/港股，优先使用 IBKR 新闻，失败后再使用其他搜索引擎：

```python
def search_stock_news(self, stock_code: str, stock_name: str, max_results: int = 5):
    """搜索股票新闻"""
    # 美股/港股优先使用 IBKR
    if self._is_foreign_stock(stock_code) and self._is_ibkr_news_available():
        ibkr_response = self._search_ibkr_news(stock_code, stock_name, max_results)
        if ibkr_response.success and len(ibkr_response.results) >= 3:
            return ibkr_response
    
    # 降级到其他搜索引擎
    return self._run_provider_search(...)
```

### 实现示例

在 `src/search_service.py` 中添加以下方法：

```python
def _is_ibkr_news_available(self) -> bool:
    """检查 IBKR 新闻是否可用"""
    try:
        from src.news_providers import IBKRNewsProvider
        provider = IBKRNewsProvider()
        return provider.is_available()
    except Exception:
        return False

def _search_ibkr_news(
    self,
    stock_code: str,
    stock_name: str,
    max_results: int = 5
) -> SearchResponse:
    """使用 IBKR 获取新闻"""
    try:
        from src.news_providers import get_ibkr_news
        
        news_list = get_ibkr_news(stock_code, max_results=max_results, days=7)
        
        if not news_list:
            return SearchResponse(
                query=f"{stock_name} 新闻",
                results=[],
                provider="IBKR",
                success=False,
                error_message="未找到相关新闻"
            )
        
        # 转换为 SearchResult 格式
        results = []
        for news in news_list:
            results.append(SearchResult(
                title=news['headline'],
                snippet=f"来源: {news['provider_name']}",
                url="",  # IBKR 新闻没有 URL
                source=news['provider_name'],
                published_date=news['time'],
            ))
        
        return SearchResponse(
            query=f"{stock_name} 新闻",
            results=results,
            provider="IBKR",
            success=True,
        )
        
    except Exception as e:
        logger.error(f"[IBKR News] 获取新闻失败: {e}")
        return SearchResponse(
            query=f"{stock_name} 新闻",
            results=[],
            provider="IBKR",
            success=False,
            error_message=str(e)
        )
```

---

## 故障排查

### 问题 1：连接失败

**错误信息**：
```
[IBKRNewsProvider] 连接失败: [Errno 111] Connection refused
```

**解决方法**：
1. 确认 TWS 或 IB Gateway 正在运行
2. 检查端口配置是否正确（TWS=7497, Gateway=4001/4002）
3. 确认 API 连接已启用（TWS 设置中）
4. 检查防火墙是否阻止了连接

### 问题 2：未获取到新闻提供商

**错误信息**：
```
[IBKRNewsProvider] 未获取到新闻提供商列表
```

**解决方法**：
1. 确认账户已登录并连接到 IBKR 服务器
2. 检查账户是否订阅了新闻数据服务
3. 尝试在 TWS 中手动查看新闻，确认功能可用

### 问题 3：未找到相关新闻

**错误信息**：
```
[IBKRNewsProvider] AAPL 未找到相关新闻
```

**可能原因**：
1. 股票代码格式错误
2. 查询时间范围内没有新闻
3. 新闻提供商不支持该股票

**解决方法**：
1. 确认股票代码格式正确（美股：`AAPL`，港股：`0700.HK`，A股：`600519`）
2. 扩大查询时间范围（增加 `days` 参数）
3. 尝试不同的新闻提供商

### 问题 4：ib_insync 未安装

**错误信息**：
```
[IBKRNewsProvider] ib_insync 未安装，IBKR 新闻功能不可用
```

**解决方法**：
```bash
pip install ib_insync
```

### 问题 5：Client ID 冲突

**错误信息**：
```
[IBKRNewsProvider] 连接失败: clientId 1 already in use
```

**解决方法**：
1. 修改 `IBKR_CLIENT_ID` 为其他值（1-32之间）
2. 或者断开其他使用相同 Client ID 的连接

---

## 测试

### 运行测试脚本

```bash
# 测试美股
python tests/test_ibkr_news.py AAPL

# 测试港股
python tests/test_ibkr_news.py 0700.HK

# 测试 A股（通过港股通）
python tests/test_ibkr_news.py 600519

# 指定参数
python tests/test_ibkr_news.py AAPL 20 14  # 最多20条，查询14天
```

### 预期输出

```
IBKR 新闻功能测试
============================================================
股票代码: AAPL
最大数量: 10
查询天数: 7
============================================================

============================================================
测试 1: 获取新闻提供商列表
============================================================
✅ 成功获取 5 个新闻提供商：
   - BRFUPDN
   - BRFG
   - DJ-N
   - DJ-RT
   - FLY

============================================================
测试 2: 获取 AAPL 的新闻
============================================================
查询参数：
  股票代码: AAPL
  最大数量: 10
  查询天数: 7

✅ 成功获取 8 条新闻：

[1] Apple announces new iPhone 16 with AI features
    时间: 2026-04-23T10:30:00Z
    来源: Dow Jones (DJ-N)
    ID: DJ-N$20260423-1030-001

[2] AAPL stock rises 2% on strong earnings report
    时间: 2026-04-22T14:15:00Z
    来源: Briefing.com (BRFUPDN)
    ID: BRFUPDN$20260422-1415-002

...

============================================================
测试 3: 获取新闻文章完整内容
============================================================
文章 ID: DJ-N$20260423-1030-001
提供商: DJ-N

✅ 成功获取文章内容（1234 字符）：

Apple Inc. announced today the launch of its new iPhone 16 series,
featuring advanced AI capabilities powered by the company's latest
A18 chip. The new devices include...

... (还有 734 字符)

============================================================
✅ 所有测试完成
============================================================
```

---

## 相关文档

- [IBKR 配置指南](./IBKR_SETUP.md) - IBKR 数据源配置
- [数据源优先级](./DATA_SOURCE_PRIORITY.md) - 数据源优先级与降级策略
- [IB API 文档](https://interactivebrokers.github.io/tws-api/) - IBKR 官方 API 文档
- [ib_insync 文档](https://ib-insync.readthedocs.io/) - ib_insync 库文档

---

## 更新日志

- 2026-04-23：初始版本，实现 IBKR 新闻功能集成
