"""
向量数据库管理模块
负责向量数据库的连接、集合管理、数据存储和查询
"""
from typing import Optional, List, Dict, Any, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import loguru
import uuid
import asyncio

logger = loguru.logger


class VectorDB:
    """向量数据库管理器，基于 Qdrant"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "events",
        vector_dim: int = 1024,
        use_memory: bool = False
    ):
        """
        初始化向量数据库管理器
        
        Args:
            host: Qdrant 服务地址
            port: Qdrant 服务端口
            collection_name: 集合名称
            vector_dim: 向量维度
            use_memory: 是否使用内存模式（测试用）
        """
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        
        # 初始化 Qdrant 客户端
        if use_memory:
            logger.info("初始化向量数据库 (内存模式)")
            self.client = QdrantClient(":memory:")
        else:
            logger.info(f"初始化向量数据库: {host}:{port}")
            self.client = QdrantClient(host=host, port=port)
        
        # 确保集合存在
        self._ensure_collection()
        
        logger.info(f"向量数据库初始化完成: collection={collection_name}, dim={vector_dim}")
    
    def _ensure_collection(self):
        """确保集合存在，不存在则创建"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"集合 '{self.collection_name}' 不存在，正在创建...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"集合 '{self.collection_name}' 创建成功")
            else:
                logger.info(f"集合 '{self.collection_name}' 已存在")
                
        except Exception as e:
            logger.error(f"确保集合存在时出错: {e}")
            raise
    
    async def add_point(
        self,
        vector: List[float],
        payload: Dict[str, Any],
        point_id: Optional[str] = None
    ) -> str:
        """异步添加单个数据点到向量数据库"""
        try:
            if point_id is None:
                point_id = str(uuid.uuid4())
            
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)]
            )
            
            logger.debug(f"数据点已添加: id={point_id}")
            return point_id
            
        except Exception as e:
            logger.error(f"添加数据点失败: {e}")
            raise
    
    async def add_points_batch(
        self, 
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        point_ids: Optional[List[str]] = None
    ) -> List[str]:
        """异步批量添加数据点"""
        try:
            if len(vectors) != len(payloads):
                raise ValueError("vectors 和 payloads 长度必须相同")
            
            if point_ids is None:
                point_ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
            elif len(point_ids) != len(vectors):
                raise ValueError("point_ids 长度必须与 vectors 相同")
            
            points = [
                PointStruct(id=point_ids[i], vector=vectors[i], payload=payloads[i])
                for i in range(len(vectors))
            ]
            
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"批量添加完成: {len(points)} 个数据点")
            return point_ids
            
        except Exception as e:
            logger.error(f"批量添加数据点失败: {e}")
            raise
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filters: 过滤条件（暂不实现，在应用层过滤）
            
        Returns:
            搜索结果列表，每个结果包含 id, score, payload
        """
        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=None,  # 在应用层过滤
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.debug(f"搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def search_async(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        异步向量相似度搜索
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filters: 过滤条件（暂不实现，在应用层过滤）
            
        Returns:
            搜索结果列表，每个结果包含 id, score, payload
        """
        # Qdrant 客户端不支持原生 async，所以使用 asyncio.to_thread 包装
        return await asyncio.to_thread(
            self.search,
            query_vector,
            limit,
            score_threshold,
            filters
        )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        获取集合信息（使用 count 接口避免版本兼容问题）
        
        Returns:
            集合信息字典
        """
        try:
            # 直接使用 count 接口，避免 get_collection 的版本兼容问题
            count_result = self.client.count(collection_name=self.collection_name)
            count = count_result.count if hasattr(count_result, 'count') else count_result
            
            return {
                "name": self.collection_name,
                "vectors_count": count,
                "points_count": count,
                "status": "available"
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {
                "name": self.collection_name,
                "vectors_count": "unknown",
                "points_count": "unknown",
                "status": "error"
            }
    
    def delete_collection(self):
        """删除集合（慎用）"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"集合 '{self.collection_name}' 已删除")
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            raise
    
    def clear_collection(self):
        """清空集合（删除所有数据点但保留集合）"""
        try:
            # 获取所有点的ID
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000  # 一次获取最多10000个
            )
            
            point_ids = [point.id for point in scroll_result[0]]
            
            if point_ids:
                # 批量删除所有点
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                logger.info(f"集合 '{self.collection_name}' 已清空，删除了 {len(point_ids)} 个数据点")
            else:
                logger.info(f"集合 '{self.collection_name}' 已经是空的")
                
        except Exception as e:
            logger.error(f"清空集合失败: {e}")
            raise
    
    def count(self) -> int:
        """
        获取集合中的数据点数量
        
        Returns:
            数据点数量
        """
        try:
            count_result = self.client.count(collection_name=self.collection_name)
            count = count_result.count if hasattr(count_result, 'count') else count_result
            return count
        except Exception as e:
            logger.error(f"获取数据点数量失败: {e}")
            return 0
    
    def list_collections(self) -> List[str]:
        """
        列出所有集合
        
        Returns:
            集合名称列表
        """
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []
    
    def create_collection(self, collection_name: str) -> bool:
        """
        创建新集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            是否创建成功
        """
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"集合 '{collection_name}' 创建成功")
            return True
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False

