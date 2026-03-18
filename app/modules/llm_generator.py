"""
LLM回复生成模块
负责基于上下文生成回复文本
"""
from typing import Optional, List, Dict, Any
from app.models import LLMResponse
from app.modules.llm import LLM
from app.models import IntentResult

import loguru

logger = loguru.logger


class LLMGenerator:
    """LLM回复生成器"""
    
    def __init__(
        self,
        api_key: str = "EMPTY",
        base_url: str = "http://YOUR_LLM_SERVER_IP:8093/v1",
        system_prompt_path: str = "conf/system_prompt_generator.txt"
    ):
        """
        初始化LLM生成器
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            system_prompt_path: 系统提示词文件路径
        """
        self.llm = LLM(
            api_key=api_key,
            base_url=base_url,
            system_promt_path=system_prompt_path
        )
        
        logger.info(f"初始化LLM生成器: base_url={base_url}")
    
    def generate(
        self,
        query: str,
        intent: Optional[IntentResult] = None,
        context: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> LLMResponse:
        """
        生成回复
        
        Args:
            query: 用户查询
            context: 检索到的上下文文档列表
            history: 对话历史
            
        Returns:
            LLM回复结果
        """
        try:
            logger.info(f"开始生成回复: query={query}")
            
            # 构建用户消息（包含上下文和历史）
            user_message = self._build_user_message(query, intent, context, history)
            
            # 调用LLM生成回复
            text = self.llm.generate(user_message)
            
            logger.info(f"response text 生成完成: {text}")
            
            return LLMResponse(
                text=text,
                finish_reason="stop"
            )
            
        except Exception as e:
            logger.error(f"LLM生成失败: {e}", exc_info=True)
            return LLMResponse(
                text="抱歉，我现在无法回答您的问题。",
                finish_reason="error"
            )
    
    def _build_user_message(
        self,
        query: str,
        intent: Optional[IntentResult] = None,
        context: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        构建用户消息（包含上下文和历史信息）
        
        Args:
            query: 用户查询
            context: 上下文文档
            history: 对话历史
            
        Returns:
            构建的用户消息
        """
        message_parts = []
        
        # 添加上下文信息
        if context and len(context) > 0:
            message_parts.append("【参考信息】")
            for i, doc in enumerate(context, 1):
                message_parts.append(f"{i}. {doc}")
            message_parts.append("")
        
        # 添加场景信息
        if intent:
            scene_name = intent.entities.get("scene_name", "")
            message_parts.append(f"【场景信息】: {scene_name}")
        
        # 添加历史对话
        if history and len(history) > 0:
            message_parts.append("【历史对话】")
            for msg in history[-3:]:  # 只保留最近3轮对话
                role = msg.get("role", "user")
                content = msg.get("content", "")
                role_label = "用户" if role == "user" else "助手"
                message_parts.append(f"{role_label}: {content}")
            message_parts.append("")
        
        # 添加当前用户问题
        message_parts.append("【用户问题】")
        message_parts.append(query)
        
        return "\n".join(message_parts)
    
    async def generate_async(
        self,
        query: str,
        intent: Optional[IntentResult] = None,
        context: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> LLMResponse:
        """
        异步生成回复
        
        Args:
            query: 用户查询
            context: 检索到的上下文文档列表
            history: 对话历史
            
        Returns:
            LLM回复结果
        """
        # 实际应用中可以调用异步的LLM API
        return self.generate(query, intent, context, history)

