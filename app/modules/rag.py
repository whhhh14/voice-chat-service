"""
RAG (Retrieval-Augmented Generation) 检索增强生成模块
负责智能检索和过滤条件提取
"""
from typing import Optional, List, Dict, Any
from app.models import RAGResult, Event
from app.modules.embedding import get_embedding_model
from app.modules.vector_db import VectorDB
from app.utils.time_utils import parse_time_range
from openai import AsyncOpenAI
from datetime import datetime
import loguru
import json
import os

logger = loguru.logger


class RAG:
    """RAG检索器"""
    
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
        similarity_threshold: float = 0.2,
        use_memory: bool = False,
        llm_api_key: str = "EMPTY",
        llm_base_url: str = "http://YOUR_LLM_SERVER_IP:8093/v1"
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
            llm_api_key: LLM API密钥
            llm_base_url: LLM API地址
        """
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        
        # 初始化向量数据库
        logger.info("初始化向量数据库...")
        self.vector_db = VectorDB(
            host=host,
            port=port,
            collection_name=collection_name,
            vector_dim=embedding_dim,
            use_memory=use_memory
        )
        
        # 初始化Embedding模型
        logger.info(f"初始化Embedding模型: {embedding_model_name}")
        self.embedding_model = get_embedding_model(
            model_name=embedding_model_name,
            api_base_url=embedding_api_base_url,
            api_key=embedding_api_key,
            embedding_dim=embedding_dim
        )
        self.embedding_dim = self.embedding_model.get_dimension()
        
        # 初始化异步LLM客户端（用于提取过滤条件）
        logger.info(f"初始化LLM客户端用于过滤条件提取: {llm_base_url}")
        self.async_llm_client = AsyncOpenAI(api_key=llm_api_key, base_url=llm_base_url)
        
        # 加载提示词模板
        self.filter_prompt_template = self._load_filter_prompt_template()
        
        logger.info(f"RAG检索器初始化完成: embedding_dim={self.embedding_dim}, top_k={top_k}")
    
    def _load_filter_prompt_template(self) -> str:
        """从配置文件加载过滤条件提取提示词模板"""
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        prompt_file = os.path.join(project_root, "conf", "rag_filter_prompt.txt")
        
        if not os.path.exists(prompt_file):
            error_msg = f"提示词配置文件不存在: {prompt_file}"
            logger.error(f"❌ {error_msg}")
            raise FileNotFoundError(error_msg)
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
            
            if not template or not template.strip():
                error_msg = f"提示词配置文件为空: {prompt_file}"
                logger.error(f"❌ {error_msg}")
                raise IOError(error_msg)
            
            logger.info(f"✅ 成功加载提示词模板: {prompt_file}")
            return template
                
        except Exception as e:
            error_msg = f"读取提示词配置文件失败: {prompt_file}, 错误: {e}"
            logger.error(f"❌ {error_msg}")
            raise IOError(error_msg) from e
    
    async def add_event(self, event: Event) -> str:
        """异步添加单个事件到向量数据库"""
        try:
            # 构建用于向量化的文本
            text_for_embedding = self._build_text_for_embedding(event)
            
            # 异步生成向量
            vector = await self.embedding_model.encode_single_async(text_for_embedding)
            
            # 准备payload
            payload = {
                "event_time": event.event_time,
                "event_type_id": event.event_type_id,
                "event_name": event.event_name,
                "event_desc": event.event_desc or "",
                "device_id": event.device_id,
                "device_name": event.device_name,
                "text_for_embedding": text_for_embedding
            }
            
            # 异步添加到向量数据库
            event_id = await self.vector_db.add_point(
                vector=vector.tolist(),
                payload=payload
            )
            
            logger.info(f"事件已添加: id={event_id}, name={event.event_name}")
            return event_id
            
        except Exception as e:
            logger.error(f"添加事件失败: {e}")
            raise
    
    async def add_events_batch(self, events: List[Event]) -> List[str]:
        """异步批量添加事件（优化版本：使用批量向量化）"""
        try:
            logger.info(f"批量添加 {len(events)} 个事件...")
            
            if not events:
                return []
            
            # 1. 构建所有文本
            texts_for_embedding = [self._build_text_for_embedding(event) for event in events]
            
            # 2. 异步批量向量化
            logger.debug(f"批量向量化 {len(texts_for_embedding)} 个文本...")
            vectors = await self.embedding_model.encode_async(texts_for_embedding)
            
            # 3. 准备 payloads
            payloads = [
                {
                    "event_time": event.event_time,
                    "event_type_id": event.event_type_id,
                    "event_name": event.event_name,
                    "event_desc": event.event_desc or "",
                    "device_id": event.device_id,
                    "device_name": event.device_name,
                    "text_for_embedding": texts_for_embedding[i]
                }
                for i, event in enumerate(events)
            ]
            
            # 4. 异步批量插入
            vectors_list = [v.tolist() for v in vectors]
            event_ids = await self.vector_db.add_points_batch(
                vectors=vectors_list,
                payloads=payloads
            )
            
            logger.info(f"批量添加完成: {len(events)} 个事件")
            return event_ids
            
        except Exception as e:
            logger.error(f"批量添加事件失败: {e}")
            raise
    
    def _build_text_for_embedding(self, event: Event) -> str:
        """构建用于向量化的文本"""
        parts = [f"事件: {event.event_name}", f"位置: {event.device_name}"]
        if event.event_desc:
            parts.append(f"描述: {event.event_desc}")
        return " | ".join(parts)
    
    async def _extract_filters_from_query_async(self, query: str) -> Optional[Dict[str, Any]]:
        """异步使用LLM从查询中自动提取过滤条件"""
        try:
            # 获取当前时间并替换到提示词模板中
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            system_prompt = self.filter_prompt_template.format(current_time=current_time)
            
            user_message = f'用户查询："{query}"\n\n请提取过滤条件（纯JSON格式）：'
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # 异步调用LLM
            response = await self.async_llm_client.chat.completions.create(
                model="Qwen3-4B-Instruct-2507",
                messages=messages,
                temperature=0.1,
                max_tokens=150
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"🤖 LLM原始输出: {content}")
            
            # 解析JSON
            if content.lower() == "null" or not content:
                logger.info("未提取到过滤条件")
                return None
            
            # 尝试提取JSON（可能包含markdown代码块）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            filters = json.loads(content)
            
            if filters and isinstance(filters, dict):
                logger.info(f"✅ 成功提取过滤条件: {filters}")
                return filters
            else:
                logger.info("提取结果为空")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ 异步提取过滤条件失败: {e}，将不使用自动过滤")
            return None
    
    async def retrieve_async(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        auto_extract_filters: bool = True
    ) -> RAGResult:
        """异步检索相关事件"""
        try:
            logger.info(f"🔍 RAG检索: {query}")
            limit = top_k or self.top_k
            
            # 1. 向量化 + 提取过滤条件
            query_vector = await self.embedding_model.encode_single_async(query)
            if filters is None and auto_extract_filters:
                filters = await self._extract_filters_from_query_async(query)
                logger.info(f"📌 过滤条件: {filters}" if filters else "💡 无过滤条件")
            
            # 2. 根据是否有时间过滤选择不同策略
            has_time_filter = filters and "time_range" in filters
            
            if has_time_filter:
                # 策略A：有时间过滤 - 时间范围内的所有事件
                logger.info("🕐 时间优先策略：获取时间范围内所有事件")
                
                # 不使用相似度阈值，获取足够多的候选
                search_results = await self.vector_db.search_async(
                    query_vector=query_vector.tolist(),
                    limit=100,  # 足够大以覆盖时间范围内所有事件
                    score_threshold=None  # 时间过滤时不使用相似度阈值
                )
                logger.info(f"📊 搜索到 {len(search_results)} 个候选")
                
                # 应用所有过滤条件（时间+其他）
                matched, _ = self._apply_filters(search_results, filters)
                logger.info(f"✅ 时间范围内匹配 {len(matched)} 个事件")
                
                # 只返回匹配的结果，不补充
                search_results = matched[:limit] if matched else []
                
            else:
                # 策略B：无时间过滤 - 标准语义搜索
                search_limit = limit * 3 if filters else limit
                search_results = await self.vector_db.search_async(
                    query_vector=query_vector.tolist(),
                    limit=search_limit,
                    score_threshold=self.similarity_threshold
                )
                logger.info(f"📊 搜索到 {len(search_results)} 个候选")
                
                # 应用过滤并合并结果
                if filters and search_results:
                    matched, unmatched = self._apply_filters(search_results, filters)
                    search_results = self._merge_filter_results(matched, unmatched, limit)
                else:
                    search_results = search_results[:limit]
            
            # 4. 构建结果
            return self._build_rag_result(search_results)
            
        except Exception as e:
            logger.error(f"RAG检索失败: {e}")
            return RAGResult(documents=["抱歉，检索失败。"], scores=[0.0], metadata=[{}])
    
    def _merge_filter_results(
        self, 
        matched: List[Dict[str, Any]], 
        unmatched: List[Dict[str, Any]], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """合并过滤后的匹配和不匹配结果"""
        logger.info(f"✅ 匹配 {len(matched)} 个，不匹配 {len(unmatched)} 个")
        if len(matched) >= limit:
            return matched[:limit]
        if matched:
            logger.info(f"⚖️ 补充 {limit - len(matched)} 个相关结果")
            return matched + unmatched[:limit - len(matched)]
        logger.warning("⚠️ 无匹配结果，返回最相关的")
        return unmatched[:limit]
    
    def _build_rag_result(self, results: List[Dict[str, Any]]) -> RAGResult:
        """构建RAG结果"""
        if not results:
            return RAGResult(
                documents=["抱歉，未找到相关事件。"],
                scores=[0.0],
                metadata=[{}]
            )
        
        documents = [self._format_document(r["payload"]) for r in results]
        scores = [r["score"] for r in results]
        metadata_list = [r["payload"] for r in results]
        
        logger.info(f"✅ 检索完成: {len(documents)} 个事件")
        return RAGResult(documents=documents, scores=scores, metadata=metadata_list)
    
    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """应用过滤条件，返回匹配和不匹配的结果"""
        matched, unmatched = [], []
        
        # 解析时间范围
        time_range = filters.get("time_range")
        start_time, end_time = parse_time_range(time_range) if time_range else (None, None)
        if start_time and end_time:
            logger.info(f"⏰ 时间范围: {start_time} ~ {end_time}")
        
        for result in results:
            payload = result["payload"]
            
            # 检查非时间字段
            non_time_match = all(
                payload.get(k) == v for k, v in filters.items() 
                if k not in ["time_range", "time_period"]
            )
            
            # 检查时间字段
            time_match = True
            if start_time and end_time:
                event_time = payload.get("event_time", "")
                time_match = bool(event_time and start_time <= event_time <= end_time)
            
            # 分类
            (matched if non_time_match and time_match else unmatched).append(result)
        
        return matched, unmatched
    
    def _format_document(self, payload: Dict[str, Any]) -> str:
        """格式化文档用于LLM"""
        parts = [
            f"时间: {payload.get('event_time', '未知')}",
            f"事件: {payload.get('event_name', '未知')}",
            f"位置: {payload.get('device_name', '未知')}"
        ]
        if payload.get('event_desc'):
            parts.append(f"详情: {payload.get('event_desc')}")
        return " | ".join(parts)
    
    # 代理方法，方便访问向量数据库功能
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        return self.vector_db.get_collection_info()
    
    def delete_collection(self):
        """删除集合"""
        self.vector_db.delete_collection()
    
    def clear_collection(self):
        """清空集合"""
        self.vector_db.clear_collection()
    
    def count(self) -> int:
        """获取数据点数量"""
        return self.vector_db.count()
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        return self.vector_db.list_collections()
    
    def create_collection(self, collection_name: str) -> bool:
        """创建新集合"""
        return self.vector_db.create_collection(collection_name)
