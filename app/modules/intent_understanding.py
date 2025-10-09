"""
LLM语义理解模块
负责理解用户意图，判断是否命中固定指令
"""
import logging
from typing import Optional, Dict, Any, List
from app.models import IntentResult, SkillType

logger = logging.getLogger(__name__)


class IntentUnderstanding:
    """意图理解器"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        初始化意图理解器
        
        Args:
            model: LLM模型名称
            api_key: API密钥
        """
        self.model = model
        self.api_key = api_key
        
        # 固定指令库
        self.fixed_commands: Dict[str, Dict[str, Any]] = {
            "打开灯": {
                "skill_id": "light_on",
                "skill_type": SkillType.COMMAND,
                "response": "好的，已为您打开灯"
            },
            "关闭灯": {
                "skill_id": "light_off",
                "skill_type": SkillType.COMMAND,
                "response": "好的，已为您关闭灯"
            },
            "打开空调": {
                "skill_id": "ac_on",
                "skill_type": SkillType.COMMAND,
                "response": "好的，已为您打开空调"
            },
            "关闭空调": {
                "skill_id": "ac_off",
                "skill_type": SkillType.COMMAND,
                "response": "好的，已为您关闭空调"
            },
            "播放音乐": {
                "skill_id": "music_play",
                "skill_type": SkillType.COMMAND,
                "response": "好的，正在为您播放音乐"
            },
            "停止播放": {
                "skill_id": "music_stop",
                "skill_type": SkillType.COMMAND,
                "response": "好的，已停止播放"
            },
            "今天天气": {
                "skill_id": "weather_query",
                "skill_type": SkillType.COMMAND,
                "response": "今天天气晴朗，温度适宜"
            },
        }
        
        logger.info(f"初始化意图理解器: model={model}")
    
    def understand(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """
        理解用户意图
        
        Args:
            text: 用户输入文本
            context: 上下文信息
            
        Returns:
            意图识别结果
        """
        try:
            logger.info(f"开始意图理解: {text}")
            
            # 1. 首先检查是否命中固定指令
            for command, config in self.fixed_commands.items():
                if command in text or self._is_similar(text, command):
                    logger.info(f"命中固定指令: {command}")
                    return IntentResult(
                        skill_id=config["skill_id"],
                        skill_type=config["skill_type"],
                        confidence=0.95,
                        entities={"response": config["response"]},
                        is_fixed_command=True
                    )
            
            # 2. 未命中固定指令，判断意图类型
            # 这里可以调用LLM进行更复杂的意图识别
            skill_id, skill_type = self._classify_intent(text, context)
            
            logger.info(f"意图识别完成: skill_id={skill_id}, skill_type={skill_type}")
            
            return IntentResult(
                skill_id=skill_id,
                skill_type=skill_type,
                confidence=0.85,
                entities={},
                is_fixed_command=False
            )
            
        except Exception as e:
            logger.error(f"意图理解失败: {e}")
            # 返回默认的聊天意图
            return IntentResult(
                skill_id="chat",
                skill_type=SkillType.CHAT,
                confidence=0.5,
                entities={},
                is_fixed_command=False
            )
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        判断两个文本是否相似
        
        Args:
            text1: 文本1
            text2: 文本2
            threshold: 相似度阈值
            
        Returns:
            是否相似
        """
        # 简单的包含判断
        # 实际应用中可以使用更复杂的相似度算法
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text2 in text1 or text1 in text2:
            return True
        
        # 计算字符重叠率
        common = set(text1) & set(text2)
        similarity = len(common) / max(len(set(text1)), len(set(text2)))
        
        return similarity >= threshold
    
    def _classify_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> tuple:
        """
        分类意图类型
        
        Args:
            text: 文本
            context: 上下文
            
        Returns:
            (skill_id, skill_type)
        """
        # 简单的关键词匹配
        # 实际应用中应该使用LLM或意图分类模型
        
        # 问答类关键词
        qa_keywords = ["什么", "为什么", "怎么", "如何", "是什么", "在哪", "哪里", "谁"]
        if any(keyword in text for keyword in qa_keywords):
            return "qa", SkillType.QA
        
        # 默认为聊天
        return "chat", SkillType.CHAT
    
    async def understand_async(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """
        异步理解用户意图
        
        Args:
            text: 用户输入文本
            context: 上下文信息
            
        Returns:
            意图识别结果
        """
        # 实际应用中可以调用异步的LLM服务
        return self.understand(text, context)

