"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class MessageType(str, Enum):
    """消息类型"""
    AUDIO = "audio"
    TEXT = "text"
    RESULT = "result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class SkillType(str, Enum):
    """技能类型"""
    COMMAND = "command"  # 固定指令
    QA = "qa"  # 问答
    CHAT = "chat"  # 闲聊


class AudioMessage(BaseModel):
    """音频消息"""
    type: MessageType = MessageType.AUDIO
    data: str = Field(..., description="Base64编码的PCM音频数据")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")
    is_end: bool = Field(default=False, description="是否为最后一帧")


class TextMessage(BaseModel):
    """文本消息"""
    type: MessageType = MessageType.TEXT
    text: str = Field(..., description="文本内容")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class ResultMessage(BaseModel):
    """结果消息"""
    type: MessageType = MessageType.RESULT
    skill_id: str = Field(..., description="技能ID")
    text: str = Field(..., description="回复文本")
    audio: Optional[str] = Field(default=None, description="Base64编码的音频数据")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class ErrorMessage(BaseModel):
    """错误消息"""
    type: MessageType = MessageType.ERROR
    code: int = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")


class HeartbeatMessage(BaseModel):
    """心跳消息"""
    type: MessageType = MessageType.HEARTBEAT
    timestamp: float = Field(..., description="时间戳")


class ASRResult(BaseModel):
    """ASR识别结果"""
    text: str = Field(..., description="识别的文本")
    confidence: float = Field(..., description="置信度")
    language: Optional[str] = Field(default=None, description="语言")


class IntentResult(BaseModel):
    """意图识别结果"""
    skill_id: str = Field(..., description="技能ID")
    skill_type: SkillType = Field(..., description="技能类型")
    confidence: float = Field(..., description="置信度")
    entities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="实体信息")
    is_fixed_command: bool = Field(..., description="是否为固定指令")


class RAGResult(BaseModel):
    """RAG检索结果"""
    documents: List[str] = Field(..., description="检索到的文档")
    scores: List[float] = Field(..., description="相关性分数")
    metadata: Optional[List[Dict[str, Any]]] = Field(default=None, description="文档元数据")


class LLMResponse(BaseModel):
    """LLM回复结果"""
    text: str = Field(..., description="生成的文本")
    finish_reason: Optional[str] = Field(default=None, description="完成原因")


class TTSResult(BaseModel):
    """TTS合成结果"""
    audio: bytes = Field(..., description="音频数据")
    format: str = Field(default="pcm", description="音频格式")
    sample_rate: int = Field(..., description="采样率")

