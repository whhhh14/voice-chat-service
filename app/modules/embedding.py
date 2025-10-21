"""
Embedding 文本向量化模块（使用 OpenAI 库简化版本）
"""
from typing import List, Union, Optional
import numpy as np
import loguru
from openai import OpenAI, AsyncOpenAI

logger = loguru.logger


class EmbeddingModel:
    """文本向量化模型（使用 OpenAI 库）"""
    
    def __init__(
        self, 
        model_name: str = "Qwen3-Embedding-0.6B",
        api_base_url: str = "http://localhost:8002/v1",
        api_key: str = "EMPTY",
        embedding_dim: int = 1024
    ):
        """初始化向量化模型"""
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        
        # 初始化同步和异步客户端
        self.client = OpenAI(api_key=api_key, base_url=api_base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=api_base_url)
        
        logger.info(f"✅ Embedding模型初始化: {model_name}, 维度: {embedding_dim}")
    
    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """同步编码文本为向量"""
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            # 使用 OpenAI 库调用 Embedding API
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            
            # 提取向量
            embeddings = np.array([item.embedding for item in response.data], dtype=np.float32)
            
            # 归一化
            if normalize:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / np.maximum(norms, 1e-12)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"同步编码失败: {e}")
            raise
    
    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """同步编码单个文本"""
        return self.encode([text], normalize)[0]
    
    async def encode_async(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """异步编码文本为向量"""
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            # 使用 OpenAI 异步客户端
            response = await self.async_client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            
            # 提取向量
            embeddings = np.array([item.embedding for item in response.data], dtype=np.float32)
            
            # 归一化
            if normalize:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / np.maximum(norms, 1e-12)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"异步编码失败: {e}")
            raise
    
    async def encode_single_async(self, text: str, normalize: bool = True) -> np.ndarray:
        """异步编码单个文本"""
        return (await self.encode_async([text], normalize))[0]
    
    def get_dimension(self) -> int:
        """返回向量维度"""
        return self.embedding_dim
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


# 全局单例
_embedding_model = None


def get_embedding_model(
    model_name: str = "Qwen3-Embedding-0.6B",
    api_base_url: str = "http://localhost:8002/v1",
    api_key: str = "EMPTY",
    embedding_dim: int = 1024
) -> EmbeddingModel:
    """获取全局Embedding模型单例"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel(
            model_name=model_name,
            api_base_url=api_base_url,
            api_key=api_key,
            embedding_dim=embedding_dim
        )
    return _embedding_model

