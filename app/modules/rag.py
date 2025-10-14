"""
RAG (Retrieval-Augmented Generation) 检索增强生成模块
负责从向量数据库中检索相关事件信息
"""
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.models import RAGResult, Event
from app.modules.embedding import get_embedding_model
import loguru
import uuid

logger = loguru.logger


class RAG:
    """RAG检索器，基于Qdrant向量数据库"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "events",
        embedding_model_name: str = "Qwen3-Embedding-0.6B",
        embedding_api_base_url: str = "http://localhost:8002/v1",
        embedding_api_key: str = "EMPTY",
        embedding_dim: int = 1024,
        top_k: int = 3,
        similarity_threshold: float = 0.5,
        use_memory: bool = True
    ):
        """
        初始化RAG检索器
        
        Args:
            host: Qdrant服务地址
            port: Qdrant服务端口
            collection_name: 集合名称
            embedding_model_name: Embedding模型名称
            embedding_api_base_url: Embedding API地址
            embedding_api_key: Embedding API密钥
            embedding_dim: 向量维度
            top_k: 返回top-k个最相关的文档
            similarity_threshold: 相似度阈值
            use_memory: 是否使用内存模式（开发测试用）
        """
        self.collection_name = collection_name
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        
        # 初始化Qdrant客户端
        if use_memory:
            # 内存模式，适合开发测试
            logger.info("初始化Qdrant客户端 (内存模式)")
            self.client = QdrantClient(":memory:")
        else:
            # 持久化模式，适合生产环境
            logger.info(f"初始化Qdrant客户端: {host}:{port}")
            self.client = QdrantClient(host=host, port=port)
        
        # 初始化Embedding模型
        logger.info(f"初始化Embedding模型: {embedding_model_name}")
        logger.info(f"Embedding API: {embedding_api_base_url}")
        
        self.embedding_model = get_embedding_model(
            model_name=embedding_model_name,
            api_base_url=embedding_api_base_url,
            api_key=embedding_api_key,
            embedding_dim=embedding_dim
        )
        self.embedding_dim = self.embedding_model.get_dimension()
        
        # 确保集合存在
        self._ensure_collection()
        
        logger.info(f"RAG检索器初始化完成: collection={collection_name}, "
                   f"embedding_dim={self.embedding_dim}, top_k={top_k}")
    
    def _ensure_collection(self):
        """确保集合存在，不存在则创建"""
        try:
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"集合 '{self.collection_name}' 不存在，正在创建...")
                
                # 创建集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE  # 使用余弦相似度
                    )
                )
                logger.info(f"集合 '{self.collection_name}' 创建成功")
            else:
                logger.info(f"集合 '{self.collection_name}' 已存在")
                
        except Exception as e:
            logger.error(f"确保集合存在时出错: {e}")
            raise
    
    def add_event(self, event: Event) -> str:
        """
        添加单个事件到向量数据库
        
        Args:
            event: 事件对象
            
        Returns:
            事件ID
        """
        try:
            # 生成事件ID
            event_id = str(uuid.uuid4())
            
            # 构建用于向量化的文本
            # 组合事件名称、描述和设备信息
            text_for_embedding = self._build_text_for_embedding(event)
            
            # 生成向量
            vector = self.embedding_model.encode_single(text_for_embedding)
            
            # 准备payload（事件元数据）
            payload = {
                "event_time": event.event_time,
                "event_type_id": event.event_type_id,
                "event_name": event.event_name,
                "event_desc": event.event_desc or "",
                "device_id": event.device_id,
                "device_name": event.device_name,
                "text_for_embedding": text_for_embedding
            }
            
            # 插入数据点
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=event_id,
                        vector=vector.tolist(),
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"事件已添加: id={event_id}, name={event.event_name}")
            return event_id
            
        except Exception as e:
            logger.error(f"添加事件失败: {e}")
            raise
    
    def add_events_batch(self, events: List[Event]) -> List[str]:
        """
        批量添加事件（优化版本：使用批量向量化）
        
        Args:
            events: 事件列表
            
        Returns:
            事件ID列表
        """
        try:
            logger.info(f"批量添加 {len(events)} 个事件...")
            
            if not events:
                return []
            
            # 1. 先构建所有文本
            texts_for_embedding = []
            for event in events:
                text = self._build_text_for_embedding(event)
                texts_for_embedding.append(text)
            
            # 2. 批量向量化（一次性编码所有文本，性能提升显著）
            logger.debug(f"批量向量化 {len(texts_for_embedding)} 个文本...")
            vectors = self.embedding_model.encode(texts_for_embedding)
            
            # 3. 构建 points
            points = []
            event_ids = []
            
            for i, event in enumerate(events):
                # 生成事件ID
                event_id = str(uuid.uuid4())
                event_ids.append(event_id)
                
                # 准备payload
                payload = {
                    "event_time": event.event_time,
                    "event_type_id": event.event_type_id,
                    "event_name": event.event_name,
                    "event_desc": event.event_desc or "",
                    "device_id": event.device_id,
                    "device_name": event.device_name,
                    "text_for_embedding": texts_for_embedding[i]
                }
                
                points.append(
                    PointStruct(
                        id=event_id,
                        vector=vectors[i].tolist(),
                        payload=payload
                    )
                )
            
            # 4. 批量插入
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"批量添加完成: {len(events)} 个事件")
            return event_ids
            
        except Exception as e:
            logger.error(f"批量添加事件失败: {e}")
            raise
    
    def _build_text_for_embedding(self, event: Event) -> str:
        """
        构建用于向量化的文本
        
        Args:
            event: 事件对象
            
        Returns:
            组合后的文本
        """
        parts = [
            f"事件: {event.event_name}",
            f"位置: {event.device_name}",
        ]
        
        if event.event_desc:
            parts.append(f"描述: {event.event_desc}")
        
        return " | ".join(parts)
    
    def retrieve(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> RAGResult:
        """
        检索相关事件
        
        Args:
            query: 查询文本
            context: 上下文信息（暂未使用）
            filters: 过滤条件，如 {"device_id": 1, "event_type_id": 1}
            top_k: 返回结果数量，如果不指定则使用默认值
            
        Returns:
            RAG检索结果
        """
        try:
            logger.info(f"开始RAG检索: {query}")
            
            # 使用传入的 top_k 或默认值
            limit = top_k if top_k is not None else self.top_k
            
            # 将查询转换为向量
            query_vector = self.embedding_model.encode_single(query)
            
            # 构建过滤条件
            query_filter = None
            if filters:
                must_conditions = []
                for key, value in filters.items():
                    must_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if must_conditions:
                    query_filter = Filter(must=must_conditions)
            
            # 执行搜索
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                query_filter=query_filter,
                limit=limit,
                score_threshold=self.similarity_threshold
            )
            
            logger.info(f"原始搜索返回 {len(search_results)} 个结果")
            
            # 提取结果
            documents = []
            scores = []
            metadata_list = []
            
            for result in search_results:
                payload = result.payload
                logger.info(f"检索到文档，相似度: {result.score:.4f}, 阈值: {self.similarity_threshold}")
                
                # 构建文档文本
                doc_text = self._format_document(payload)
                documents.append(doc_text)
                scores.append(result.score)
                metadata_list.append(payload)
            
            if not documents:
                logger.warning(f"未找到相关事件（阈值={self.similarity_threshold}）")
                documents = ["抱歉，我没有找到相关的事件信息。"]
                scores = [0.0]
                metadata_list = [{}]
            
            logger.info(f"检索完成: 找到 {len(documents)} 个相关事件")
            
            return RAGResult(
                documents=documents,
                scores=scores,
                metadata=metadata_list
            )
            
        except Exception as e:
            logger.error(f"RAG检索失败: {e}")
            return RAGResult(
                documents=["抱歉，检索过程中出现错误。"],
                scores=[0.0],
                metadata=[{}]
            )
    
    def _format_document(self, payload: Dict[str, Any]) -> str:
        """
        格式化文档用于LLM
        
        Args:
            payload: 事件payload
            
        Returns:
            格式化后的文档字符串
        """
        parts = [
            f"时间: {payload.get('event_time', '未知')}",
            f"事件: {payload.get('event_name', '未知')}",
            f"位置: {payload.get('device_name', '未知')}"
        ]
        
        if payload.get('event_desc'):
            parts.append(f"详情: {payload.get('event_desc')}")
        
        return " | ".join(parts)
    
    async def retrieve_async(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> RAGResult:
        """
        异步检索相关事件
        
        Args:
            query: 查询文本
            context: 上下文信息
            filters: 过滤条件
            top_k: 返回结果数量
            
        Returns:
            RAG检索结果
        """
        # Qdrant client目前是同步的，这里简单包装
        # 实际生产环境可以使用异步版本的client
        return self.retrieve(query, context, filters, top_k)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        获取集合信息
        
        Returns:
            集合信息字典
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {}
    
    def delete_collection(self):
        """删除集合（慎用）"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"集合 '{self.collection_name}' 已删除")
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            raise


if __name__ == "__main__":
    # 测试代码
    # 注意：运行前需要确保 Embedding API 服务已启动
    from app.models import Event
    
    # 初始化RAG
    rag = RAG(
        use_memory=True,
        embedding_model_name="Qwen3-Embedding-0.6B",
        embedding_api_base_url="http://localhost:8002/v1",
        embedding_dim=1024
    )
    
    # 创建测试事件
    test_events = [
        Event(
            event_time="2025-10-13 10:10:01",
            event_type_id=1,
            event_name="快递送达",
            event_desc="一个穿红衣服的男子送达了快递",
            device_id=1,
            device_name="门口"
        ),
        Event(
            event_time="2025-10-13 10:15:20",
            event_type_id=1,
            event_name="快递取走",
            event_desc="有人从门口取走了快递",
            device_id=1,
            device_name="门口"
        ),
        Event(
            event_time="2025-10-13 14:30:45",
            event_type_id=1,
            event_name="宝宝哭泣",
            event_desc="婴儿在卧室里哭泣",
            device_id=2,
            device_name="卧室"
        )
    ]
    
    # 批量添加事件
    event_ids = rag.add_events_batch(test_events)
    print(f"添加了 {len(event_ids)} 个事件")
    
    # 查看集合信息
    info = rag.get_collection_info()
    print(f"集合信息: {info}")
    
    # 测试检索
    query = "门口有什么事情发生？"
    result = rag.retrieve(query)
    print(f"\n查询: {query}")
    print(f"找到 {len(result.documents)} 个相关事件:")
    for i, (doc, score) in enumerate(zip(result.documents, result.scores)):
        print(f"{i+1}. [相似度: {score:.4f}] {doc}")
