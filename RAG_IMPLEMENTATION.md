# RAG 模块实现文档

## 概述

本项目已成功实现 RAG (Retrieval-Augmented Generation) 模块，用于智能事件检索和问答。系统使用 Qdrant 向量数据库存储事件数据，并通过 Sentence Transformers 实现文本向量化。

## 功能特性

- ✅ **向量数据库**: 基于 Qdrant 的高性能向量存储
- ✅ **文本向量化**: 使用多语言 Sentence Transformers 模型
- ✅ **事件管理**: 完整的事件增删改查功能
- ✅ **智能检索**: 基于语义相似度的事件检索
- ✅ **过滤查询**: 支持按设备、事件类型等条件过滤
- ✅ **批量操作**: 支持批量导入事件数据
- ✅ **RESTful API**: 提供完整的 HTTP API 接口

## 系统架构

```
┌─────────────────┐
│   用户查询      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Embedding      │ (文本向量化)
│  Model          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Qdrant         │ (向量数据库)
│  Vector DB      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  相似度检索     │
│  Top-K Results  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM 生成回复   │
└─────────────────┘
```

## 事件数据模型

### Event 字段说明

| 字段名 | 类型 | 必须 | 说明 | 示例 |
|--------|------|------|------|------|
| event_time | str | 是 | 事件发生时间 | 2025-10-13 10:10:01 |
| event_type_id | int | 是 | 事件类型ID (1:已定义 2:未定义) | 1 |
| event_name | str | 是 | 事件名称 | 快递送达 |
| event_desc | str | 否 | 事件描述 | 一个穿红衣服的男子送达了快递 |
| device_id | int | 是 | 设备ID | 1 |
| device_name | str | 是 | 设备位置 | 门口 |

### 示例数据

```json
{
    "event_time": "2025-10-13 10:10:01",
    "event_type_id": 1,
    "event_name": "快递送达",
    "event_desc": "一个穿红衣服的男子送达了快递",
    "device_id": 1,
    "device_name": "门口"
}
```

## 安装依赖

```bash
pip install qdrant-client sentence-transformers torch transformers openai loguru
```

或直接安装项目依赖：

```bash
pip install -r requirements.txt
```

## 配置说明

在 `.env` 文件中配置 RAG 相关参数：

```bash
# RAG配置
RAG_TOP_K=3                                              # 返回结果数量
RAG_SIMILARITY_THRESHOLD=0.7                             # 相似度阈值
RAG_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2  # Embedding模型

# Qdrant配置
QDRANT_HOST=localhost                                    # Qdrant服务地址
QDRANT_PORT=6333                                        # Qdrant服务端口
QDRANT_COLLECTION_NAME=events                           # 集合名称
QDRANT_USE_MEMORY=True                                  # 是否使用内存模式
```

### 配置项说明

- **RAG_TOP_K**: 检索返回的最大结果数量
- **RAG_SIMILARITY_THRESHOLD**: 相似度阈值(0-1)，低于此值的结果会被过滤
- **RAG_EMBEDDING_MODEL**: 文本向量化模型名称
- **QDRANT_USE_MEMORY**: 
  - `True`: 内存模式，适合开发测试
  - `False`: 持久化模式，适合生产环境

### 推荐的 Embedding 模型

| 模型名称 | 语言 | 维度 | 特点 |
|---------|------|------|------|
| paraphrase-multilingual-MiniLM-L12-v2 | 多语言 | 384 | 轻量级，速度快 |
| paraphrase-multilingual-mpnet-base-v2 | 多语言 | 768 | 高精度 |
| all-MiniLM-L6-v2 | 英文 | 384 | 英文专用，轻量 |

## 使用方法

### 1. 导入示例数据

运行导入脚本，将示例事件数据导入向量数据库：

```bash
python scripts/import_events.py
```

该脚本会：
- 创建 25+ 个示例事件（快递、宝宝、访客、宠物等）
- 将事件导入 Qdrant 向量数据库
- 执行测试查询验证功能

### 2. 测试 RAG 功能

运行测试脚本：

```bash
python scripts/test_rag.py
```

测试内容包括：
- 基本功能测试（添加、检索）
- 搜索功能测试
- 过滤条件测试
- 向量相似度测试
- 集成测试

### 3. 使用 API

启动服务：

```bash
python -m app.main
```

#### 创建单个事件

```bash
curl -X POST "http://localhost:8000/api/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_time": "2025-10-13 10:10:01",
    "event_type_id": 1,
    "event_name": "快递送达",
    "event_desc": "一个穿红衣服的男子送达了快递",
    "device_id": 1,
    "device_name": "门口"
  }'
```

#### 批量创建事件

```bash
curl -X POST "http://localhost:8000/api/events/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_time": "2025-10-13 10:10:01",
      "event_type_id": 1,
      "event_name": "快递送达",
      "event_desc": "快递员送来包裹",
      "device_id": 1,
      "device_name": "门口"
    },
    {
      "event_time": "2025-10-13 14:30:45",
      "event_type_id": 1,
      "event_name": "宝宝哭泣",
      "event_desc": "婴儿在卧室哭泣",
      "device_id": 2,
      "device_name": "卧室"
    }
  ]'
```

#### 搜索事件

```bash
curl -X POST "http://localhost:8000/api/events/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "今天门口有快递吗？",
    "top_k": 5
  }'
```

#### 带过滤条件搜索

```bash
curl -X POST "http://localhost:8000/api/events/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "有什么事情发生？",
    "top_k": 5,
    "filters": {
      "device_id": 1
    }
  }'
```

#### 获取集合信息

```bash
curl -X GET "http://localhost:8000/api/events/collection/info"
```

### 4. Python 代码示例

```python
from app.models import Event
from app.modules.rag import RAG

# 初始化RAG
rag = RAG(use_memory=True)

# 创建事件
event = Event(
    event_time="2025-10-13 10:10:01",
    event_type_id=1,
    event_name="快递送达",
    event_desc="一个穿红衣服的男子送达了快递",
    device_id=1,
    device_name="门口"
)

# 添加事件
event_id = rag.add_event(event)
print(f"事件已添加: {event_id}")

# 批量添加
events = [event1, event2, event3]
event_ids = rag.add_events_batch(events)

# 检索事件
result = rag.retrieve("今天门口有快递吗？")
for doc, score in zip(result.documents, result.scores):
    print(f"[{score:.4f}] {doc}")

# 带过滤条件检索
result = rag.retrieve(
    query="有什么事情发生？",
    filters={"device_id": 1}
)

# 查看集合信息
info = rag.get_collection_info()
print(f"集合信息: {info}")
```

## 工作原理

### 1. 文本向量化

事件数据在存储前会被转换为向量：

```python
# 组合事件信息
text = f"事件: {event_name} | 位置: {device_name} | 描述: {event_desc}"

# 转换为向量
vector = embedding_model.encode(text)  # 384维向量
```

### 2. 向量存储

向量和元数据一起存储在 Qdrant 中：

```python
{
    "id": "uuid",
    "vector": [0.1, 0.2, ...],  # 384维
    "payload": {
        "event_time": "2025-10-13 10:10:01",
        "event_name": "快递送达",
        "device_name": "门口",
        ...
    }
}
```

### 3. 语义检索

用户查询时：

1. 查询文本被转换为向量
2. 在向量数据库中搜索最相似的向量（余弦相似度）
3. 返回 Top-K 个最相关的事件
4. 结果传递给 LLM 生成回答

```python
query = "今天门口有快递吗？"
query_vector = embedding_model.encode(query)
results = qdrant.search(query_vector, top_k=3)
# 返回最相关的3个事件
```

## 性能优化

### 1. 批量操作

使用批量接口可以大幅提升性能：

```python
# ✓ 好：批量添加
rag.add_events_batch(events)  # 一次性添加多个事件

# ✗ 差：逐个添加
for event in events:
    rag.add_event(event)  # 多次网络请求
```

### 2. 向量缓存

Embedding 模型会自动缓存，避免重复加载：

```python
# 全局单例
embedding_model = get_embedding_model()  # 只加载一次
```

### 3. 相似度阈值

调整阈值可以平衡精度和召回率：

```python
# 高精度，低召回
rag = RAG(similarity_threshold=0.8)

# 低精度，高召回
rag = RAG(similarity_threshold=0.5)
```

## 常见问题

### Q1: 如何选择 Embedding 模型？

**A**: 
- 多语言场景：`paraphrase-multilingual-MiniLM-L12-v2`
- 高精度需求：`paraphrase-multilingual-mpnet-base-v2`
- 英文场景：`all-MiniLM-L6-v2`

### Q2: 内存模式 vs 持久化模式？

**A**:
- **内存模式** (`use_memory=True`): 
  - 优点：快速、适合开发测试
  - 缺点：重启后数据丢失
- **持久化模式** (`use_memory=False`):
  - 优点：数据持久化
  - 缺点：需要运行 Qdrant 服务

### Q3: 如何运行 Qdrant 服务？

**A**:

使用 Docker：

```bash
docker run -p 6333:6333 qdrant/qdrant
```

或使用 Docker Compose（推荐）：

```yaml
version: '3'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data:/qdrant/storage
```

### Q4: 向量维度是什么？

**A**: 向量维度取决于 Embedding 模型：
- MiniLM 模型：384 维
- MPNet 模型：768 维
- 维度越高，表达能力越强，但计算成本也越高

### Q5: 如何提高检索精度？

**A**:
1. 使用更好的 Embedding 模型（如 MPNet）
2. 调整相似度阈值
3. 丰富事件描述信息
4. 使用过滤条件缩小搜索范围

## 扩展开发

### 1. 自定义 Embedding 模型

```python
from app.modules.embedding import EmbeddingModel

# 使用自定义模型
model = EmbeddingModel("your-custom-model")
```

### 2. 添加新的过滤条件

在 `rag.py` 中扩展过滤逻辑：

```python
# 支持时间范围过滤
filters = {
    "device_id": 1,
    "event_type_id": 1,
    "time_range": ["2025-10-13 00:00:00", "2025-10-13 23:59:59"]
}
```

### 3. 集成其他向量数据库

目前支持 Qdrant，可以扩展支持：
- Milvus
- Pinecone
- Weaviate
- Elasticsearch

## 文件结构

```
app/
├── models.py                      # 数据模型（Event, EventSearchQuery）
├── config.py                      # 配置管理
├── main.py                        # API 端点
└── modules/
    ├── embedding.py               # 文本向量化
    └── rag.py                     # RAG 核心逻辑

scripts/
├── import_events.py               # 数据导入脚本
└── test_rag.py                    # 测试脚本

RAG_IMPLEMENTATION.md              # 本文档
```

## 下一步

- [ ] 添加事件删除功能
- [ ] 支持时间范围过滤
- [ ] 实现增量更新
- [ ] 添加事件统计分析
- [ ] 支持多模态检索（图像+文本）

## 参考资料

- [Qdrant 文档](https://qdrant.tech/documentation/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG 原理](https://arxiv.org/abs/2005.11401)

---

**版本**: 1.0.0  
**最后更新**: 2025-10-13

