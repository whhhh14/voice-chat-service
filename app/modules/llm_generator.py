"""
LLM回复生成模块
负责基于上下文生成回复文本
"""
from typing import Optional, List, Dict, Any
from app.models import LLMResponse

import loguru

logger = loguru.logger


class LLMGenerator:
    """LLM回复生成器"""
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        初始化LLM生成器
        
        Args:
            model: LLM模型名称
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大token数
        """
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"初始化LLM生成器: model={model}, temperature={temperature}")
        
        # 这里可以初始化实际的LLM客户端
        # 示例：self.client = OpenAI(api_key=api_key)
    
    def generate(
        self,
        query: str,
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
            
            # 构建提示词
            prompt = self._build_prompt(query, context, history)
            
            # TODO: 调用实际的LLM API
            # 示例：使用OpenAI
            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[{"role": "user", "content": prompt}],
            #     temperature=self.temperature,
            #     max_tokens=self.max_tokens
            # )
            # text = response.choices[0].message.content
            # finish_reason = response.choices[0].finish_reason
            
            # 模拟LLM回复
            text = self._generate_mock_response(query, context)
            finish_reason = "stop"
            
            logger.info(f"生成完成: {text[:50]}...")
            
            return LLMResponse(
                text=text,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            return LLMResponse(
                text="抱歉，我现在无法回答您的问题。",
                finish_reason="error"
            )
    
    def _build_prompt(
        self,
        query: str,
        context: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        构建提示词
        
        Args:
            query: 用户查询
            context: 上下文文档
            history: 对话历史
            
        Returns:
            构建的提示词
        """
        prompt_parts = []
        
        # 系统提示
        prompt_parts.append("你是一个智能助手，请根据提供的上下文信息回答用户的问题。")
        
        # 添加上下文
        if context:
            prompt_parts.append("\n参考信息：")
            for i, doc in enumerate(context, 1):
                prompt_parts.append(f"{i}. {doc}")
        
        # 添加历史对话
        if history:
            prompt_parts.append("\n历史对话：")
            for msg in history[-3:]:  # 只保留最近3轮对话
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
        
        # 添加用户问题
        prompt_parts.append(f"\n用户问题：{query}")
        prompt_parts.append("\n请回答：")
        
        return "\n".join(prompt_parts)
    
    def _generate_mock_response(self, query: str, context: Optional[List[str]] = None) -> str:
        """
        生成模拟回复（用于演示）
        
        Args:
            query: 用户查询
            context: 上下文文档
            
        Returns:
            模拟回复
        """
        # 如果有上下文，基于上下文生成回复
        if context and len(context) > 0:
            return f"Based on the relevant information, {context[0]} Do you have any other questions?"
        
        # Otherwise, generate a generic response
        return f"I understand that your question is about: {query}. That's a good question, let me answer it for you. In a real application, this would call the actual LLM service to generate a more accurate response."
    
    async def generate_async(
        self,
        query: str,
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
        return self.generate(query, context, history)

