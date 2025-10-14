"""
Embedding 文本向量化模块
负责将文本转换为向量表示
通过 HTTP API 调用远程 Embedding 服务
"""
from typing import List, Union, Optional
import numpy as np
import loguru
import requests
import json

logger = loguru.logger


class EmbeddingModel:
    """文本向量化模型"""
    
    def __init__(
        self, 
        model_name: str = "Qwen3-Embedding-0.6B",
        api_base_url: str = "http://localhost:8002/v1",
        api_key: str = "EMPTY",
        embedding_dim: int = 1024
    ):
        """
        初始化向量化模型
        
        Args:
            model_name: 模型名称
            api_base_url: Embedding API 基础地址
                         例如: "http://localhost:8002/v1"
            api_key: API 密钥
            embedding_dim: 向量维度（需要根据模型指定）
                          - Qwen3-Embedding-0.6B: 1024
                          - paraphrase-multilingual-MiniLM-L12-v2: 384
                          - paraphrase-multilingual-mpnet-base-v2: 768
        """
        self.model_name = model_name
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.embedding_dim = embedding_dim
        
        logger.info(f"初始化Embedding模型 (API模式): {model_name}")
        logger.info(f"API地址: {api_base_url}")
        self._init_api_mode()
    
    def _init_api_mode(self):
        """初始化 API 模式"""
        try:
            # 测试 API 连接
            test_response = self._call_embedding_api(["测试"])
            if test_response is not None:
                logger.info(f"✓ API 连接成功，向量维度: {self.embedding_dim}")
            else:
                logger.warning(f"⚠ API 测试失败，但继续使用 API 模式")
        except Exception as e:
            logger.warning(f"⚠ API 初始化警告: {e}")
    
    def _call_embedding_api(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        调用 Embedding API
        
        Args:
            texts: 文本列表
            
        Returns:
            向量数组或 None
        """
        try:
            # OpenAI 兼容的 Embedding API 格式
            url = f"{self.api_base_url}/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": self.model_name,
                "input": texts
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 提取向量
            embeddings = []
            for item in result["data"]:
                embeddings.append(item["embedding"])
            
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            return None
    
    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        将文本编码为向量
        
        Args:
            texts: 单个文本或文本列表
            normalize: 是否对向量进行归一化（推荐用于余弦相似度计算）
            
        Returns:
            文本向量，shape为(n, embedding_dim)
        """
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            logger.debug(f"编码 {len(texts)} 个文本")
            
            # 调用 API 获取向量
            embeddings = self._call_embedding_api(texts)
            if embeddings is None:
                raise RuntimeError("API 调用失败")
            
            # 归一化（如果需要）
            if normalize:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / np.maximum(norms, 1e-12)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            raise
    
    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        编码单个文本
        
        Args:
            text: 文本内容
            normalize: 是否归一化
            
        Returns:
            文本向量，shape为(embedding_dim,)
        """
        embeddings = self.encode([text], normalize=normalize)
        return embeddings[0]
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.embedding_dim
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度 (-1 到 1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


# 全局单例实例
_embedding_model = None


def get_embedding_model(
    model_name: str = "Qwen3-Embedding-0.6B",
    api_base_url: str = "http://localhost:8002/v1",
    api_key: str = "EMPTY",
    embedding_dim: int = 1024
) -> EmbeddingModel:
    """
    获取全局Embedding模型单例
    
    Args:
        model_name: 模型名称
        api_base_url: API 基础地址
        api_key: API 密钥
        embedding_dim: 向量维度
        
    Returns:
        EmbeddingModel实例
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel(
            model_name=model_name,
            api_base_url=api_base_url,
            api_key=api_key,
            embedding_dim=embedding_dim
        )
    return _embedding_model


if __name__ == "__main__":
    # 测试代码
    # 注意：运行前需要确保 Embedding API 服务已启动
    model = EmbeddingModel(
        model_name="Qwen3-Embedding-0.6B",
        api_base_url="http://localhost:8002/v1",
        api_key="EMPTY",
        embedding_dim=1024
    )
    
    # 测试单个文本
    text = "今天天气真不错"
    vector = model.encode_single(text)
    print(f"文本: {text}")
    print(f"向量维度: {vector.shape}")
    print(f"向量前5维: {vector[:5]}")
    
    # 测试多个文本
    texts = [
        "快递已送达门口",
        "快递员送来包裹",
        "宝宝正在哭泣"
    ]
    vectors = model.encode(texts)
    print(f"\n批量编码 {len(texts)} 个文本")
    print(f"向量矩阵形状: {vectors.shape}")
    
    # 测试相似度
    sim = model.cosine_similarity(vectors[0], vectors[1])
    print(f"\n文本1和文本2的相似度: {sim:.4f}")
    
    sim = model.cosine_similarity(vectors[0], vectors[2])
    print(f"文本1和文本3的相似度: {sim:.4f}")

